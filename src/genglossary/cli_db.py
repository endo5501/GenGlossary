"""Database CLI commands for GenGlossary."""

from contextlib import contextmanager
from pathlib import Path
from typing import Callable

import click
import sqlite3
from rich.console import Console
from rich.table import Table

from genglossary.llm.factory import create_llm_client
from genglossary.db.connection import database_connection, transaction
from genglossary.db.document_repository import list_all_documents
from genglossary.db.issue_repository import delete_all_issues, list_all_issues, create_issue
from genglossary.db.models import GlossaryTermRow
from genglossary.db.provisional_repository import (
    create_provisional_term,
    delete_all_provisional,
    get_provisional_term,
    list_all_provisional,
    update_provisional_term,
)
from genglossary.db.refined_repository import (
    create_refined_term,
    delete_all_refined,
    get_refined_term,
    list_all_refined,
    update_refined_term,
)
from genglossary.db.metadata_repository import get_metadata
from genglossary.db.schema import initialize_db
from genglossary.db.term_repository import (
    create_term,
    delete_all_terms,
    delete_term,
    get_term,
    list_all_terms,
    update_term,
)
from genglossary.document_loader import DocumentLoader
from genglossary.glossary_generator import GlossaryGenerator
from genglossary.glossary_refiner import GlossaryRefiner
from genglossary.glossary_reviewer import GlossaryReviewer
from genglossary.models.document import Document
from genglossary.models.glossary import Glossary, GlossaryIssue
from genglossary.term_extractor import TermExtractor

console = Console()


# ============================================================================
# Helper functions for regenerate commands
# ============================================================================


def _initialize_llm_client(llm_provider: str, model: str | None):
    """Initialize and validate LLM client.

    Args:
        llm_provider: LLM provider name.
        model: Model name (optional).

    Returns:
        Initialized LLM client.

    Raises:
        click.Abort: If LLM client is not available.
    """
    llm_client = create_llm_client(llm_provider, model)
    if not llm_client.is_available():
        console.print(f"[red]{llm_provider} が利用できません[/red]")
        raise click.Abort()
    return llm_client


@contextmanager
def _db_operation(db_path: str):
    """Context manager for CLI database operations with error handling.

    Wraps database_connection() with CLI-specific error handling.

    Args:
        db_path: Path to database file.

    Yields:
        Database connection.

    Handles all exceptions and displays error messages.
    """
    try:
        with database_connection(db_path) as conn:
            yield conn
    except click.Abort:
        raise
    except Exception as e:
        console.print(f"[red]エラー: {e}[/red]")
        raise click.Abort()


def _reconstruct_documents_from_db(
    doc_rows: list[sqlite3.Row],
) -> list[Document]:
    """Reconstruct Document objects from database rows.

    Args:
        doc_rows: Document rows from database.

    Returns:
        List of reconstructed Document objects.

    Warns about missing files but continues processing.
    """
    documents: list[Document] = []
    for doc_row in doc_rows:
        doc = Document(
            file_path=doc_row["file_name"],
            content=doc_row["content"],
        )
        documents.append(doc)
    return documents


def _reconstruct_glossary_from_rows(
    provisional_rows: list[GlossaryTermRow],
) -> Glossary:
    """Reconstruct Glossary object from database rows.

    Args:
        provisional_rows: Glossary term rows from database.

    Returns:
        Reconstructed Glossary object.
    """
    from genglossary.models.term import Term

    glossary = Glossary()
    for prov_row in provisional_rows:
        term = Term(
            name=prov_row["term_name"],
            definition=prov_row["definition"],
            confidence=prov_row["confidence"],
            occurrences=prov_row["occurrences"],
        )
        glossary.add_term(term)
    return glossary


def _reconstruct_issues_from_rows(
    issue_rows: list[sqlite3.Row],
) -> list[GlossaryIssue]:
    """Reconstruct GlossaryIssue objects from database rows.

    Args:
        issue_rows: Issue rows from database.

    Returns:
        List of reconstructed GlossaryIssue objects.
    """
    issues: list[GlossaryIssue] = []
    for issue_row in issue_rows:
        issue = GlossaryIssue(
            term_name=issue_row["term_name"],
            issue_type=issue_row["issue_type"],
            description=issue_row["description"],
        )
        issues.append(issue)
    return issues


def _validate_prerequisites(
    conn: sqlite3.Connection,
    required_data: list[tuple[Callable, str]],
) -> list | None:
    """Validate that required data exists in database.

    Args:
        conn: Database connection.
        required_data: List of (fetch_function, empty_message) tuples.

    Returns:
        List of fetched data if all valid, None otherwise.

    Example:
        data = _validate_prerequisites(conn, [
            (list_all_terms, "用語がありません"),
            (list_all_documents, "ドキュメントがありません"),
        ])
        if data is None:
            return
        terms, docs = data
    """
    results = []
    for fetch_func, empty_msg in required_data:
        data = fetch_func(conn)
        if not data:
            console.print(f"[yellow]{empty_msg}[/yellow]")
            return None
        results.append(data)
    return results


def _save_glossary_terms(
    conn: sqlite3.Connection,
    glossary: Glossary,
    delete_func: Callable,
    create_func: Callable,
) -> int:
    """Save glossary terms to database (clear and create pattern).

    Args:
        conn: Database connection.
        glossary: Glossary object to save.
        delete_func: Function to delete all existing terms.
        create_func: Function to create a single term.

    Returns:
        Number of terms saved.
    """
    with transaction(conn):
        delete_func(conn)
        for term in glossary.terms.values():
            create_func(conn, term.name, term.definition, term.confidence, term.occurrences)
    return len(glossary.terms)


def _save_issues(
    conn: sqlite3.Connection,
    issues: list[GlossaryIssue],
) -> int:
    """Save issues to database (clear and create pattern).

    Args:
        conn: Database connection.
        issues: List of GlossaryIssue objects to save.

    Returns:
        Number of issues saved.
    """
    with transaction(conn):
        delete_all_issues(conn)
        for issue in issues:
            create_issue(conn, issue.term_name, issue.issue_type, issue.description)
    return len(issues)


def _create_glossary_term_table(
    term_list: list[GlossaryTermRow], title: str
) -> Table:
    """Create a Rich table for glossary terms (provisional or refined).

    Args:
        term_list: List of glossary term rows.
        title: Table title.

    Returns:
        Rich Table object.
    """
    table = Table(title=title)
    table.add_column("ID", style="cyan")
    table.add_column("用語", style="magenta")
    table.add_column("定義", style="white")
    table.add_column("信頼度", style="green")

    for term in term_list:
        definition = term["definition"]
        truncated_def = definition[:50] + "..." if len(definition) > 50 else definition
        table.add_row(
            str(term["id"]),
            term["term_name"],
            truncated_def,
            f"{term['confidence']:.2f}",
        )

    return table


def _display_glossary_term_details(term: GlossaryTermRow, term_type: str) -> None:
    """Display glossary term details (provisional or refined).

    Args:
        term: Glossary term record.
        term_type: Type of term ("Provisional" or "Refined").
    """
    console.print(f"\n[bold]{term_type} Term #{term['id']}[/bold]")
    console.print(f"用語: {term['term_name']}")
    console.print(f"定義: {term['definition']}")
    console.print(f"信頼度: {term['confidence']:.2f}")


@click.group()
def db() -> None:
    """Database management commands."""
    pass


@db.command()
@click.option(
    "--path",
    type=click.Path(),
    default="./genglossary.db",
    help="Path to database file (default: ./genglossary.db)",
)
def init(path: str) -> None:
    """Initialize database schema.

    Creates a new SQLite database with all required tables.
    If the database already exists, this command is idempotent
    and will not destroy existing data.

    Example:
        genglossary db init
        genglossary db init --path ./output/glossary.db
    """
    db_path = Path(path)
    with _db_operation(str(db_path)) as conn:
        initialize_db(conn)
    console.print(f"[green]✓[/green] データベースを初期化しました: {db_path}")
    console.print(f"[dim]  親ディレクトリ: {db_path.parent.absolute()}[/dim]")


@db.command()
@click.option(
    "--db-path",
    type=click.Path(exists=True),
    default="./genglossary.db",
    help="Path to database file",
)
def info(db_path: str) -> None:
    """メタデータを表示.

    Example:
        genglossary db info
    """
    with _db_operation(db_path) as conn:
        metadata = get_metadata(conn)

    if metadata is None:
        console.print("[yellow]メタデータがありません[/yellow]")
        return

    # Display metadata
    console.print("\n[bold]メタデータ[/bold]")
    if metadata["input_path"]:
        console.print(f"入力パス: {metadata['input_path']}")
    console.print(f"LLMプロバイダー: {metadata['llm_provider']}")
    console.print(f"LLMモデル: {metadata['llm_model']}")
    console.print(f"作成日時: {metadata['created_at']}")


@db.group()
def terms() -> None:
    """抽出用語の管理コマンド."""
    pass


@terms.command("list")
@click.option(
    "--db-path",
    type=click.Path(exists=True),
    default="./genglossary.db",
    help="Path to database file",
)
def terms_list(db_path: str) -> None:
    """抽出用語一覧を表示.

    Example:
        genglossary db terms list
    """
    with _db_operation(db_path) as conn:
        term_list = list_all_terms(conn)

    if not term_list:
        console.print("[yellow]用語がありません[/yellow]")
        return

    # Create table
    table = Table(title="抽出用語")
    table.add_column("ID", style="cyan")
    table.add_column("用語", style="magenta")
    table.add_column("カテゴリ", style="green")

    for term in term_list:
        table.add_row(
            str(term["id"]),
            term["term_text"],
            term["category"] or "[dim]なし[/dim]",
        )

    console.print(table)


@terms.command("show")
@click.argument("term_id", type=int)
@click.option(
    "--db-path",
    type=click.Path(exists=True),
    default="./genglossary.db",
    help="Path to database file",
)
def terms_show(term_id: int, db_path: str) -> None:
    """指定されたterm_idの詳細を表示.

    Example:
        genglossary db terms show 1
    """
    with _db_operation(db_path) as conn:
        term = get_term(conn, term_id)

    if term is None:
        console.print(f"[red]Term ID {term_id} が見つかりません[/red]")
        raise click.Abort()

    # Display term details
    console.print(f"\n[bold]Term #{term['id']}[/bold]")
    console.print(f"用語: {term['term_text']}")
    console.print(f"カテゴリ: {term['category'] or '[dim]なし[/dim]'}")


@terms.command("update")
@click.argument("term_id", type=int)
@click.option(
    "--text",
    type=str,
    required=True,
    help="New term text",
)
@click.option(
    "--category",
    type=str,
    default=None,
    help="New category (optional)",
)
@click.option(
    "--db-path",
    type=click.Path(exists=True),
    default="./genglossary.db",
    help="Path to database file",
)
def terms_update(term_id: int, text: str, category: str | None, db_path: str) -> None:
    """用語を更新.

    Example:
        genglossary db terms update 1 --text "量子計算機" --category "technical"
    """
    with _db_operation(db_path) as conn:
        with transaction(conn):
            update_term(conn, term_id, text, category)
    console.print(f"[green]✓[/green] Term #{term_id} を更新しました")


@terms.command("delete")
@click.argument("term_id", type=int)
@click.option(
    "--db-path",
    type=click.Path(exists=True),
    default="./genglossary.db",
    help="Path to database file",
)
def terms_delete(term_id: int, db_path: str) -> None:
    """用語を削除.

    Example:
        genglossary db terms delete 1
    """
    with _db_operation(db_path) as conn:
        with transaction(conn):
            delete_term(conn, term_id)
    console.print(f"[green]✓[/green] Term #{term_id} を削除しました")


@terms.command("import")
@click.option(
    "--file",
    type=click.Path(exists=True),
    required=True,
    help="Text file with one term per line",
)
@click.option(
    "--db-path",
    type=click.Path(exists=True),
    default="./genglossary.db",
    help="Path to database file",
)
def terms_import(file: str, db_path: str) -> None:
    """テキストファイルから用語をインポート（1行1用語）.

    Example:
        genglossary db terms import --file terms.txt
    """
    # Read terms from file
    with open(file, "r", encoding="utf-8") as f:
        term_texts = [line.strip() for line in f if line.strip()]

    # Import terms
    with _db_operation(db_path) as conn:
        with transaction(conn):
            for term_text in term_texts:
                create_term(conn, term_text)

    console.print(
        f"[green]✓[/green] {len(term_texts)}件の用語をインポートしました"
    )


@terms.command("regenerate")
@click.option(
    "--input",
    type=click.Path(exists=True),
    required=True,
    help="Input directory containing documents",
)
@click.option(
    "--llm-provider",
    type=click.Choice(["ollama", "openai"], case_sensitive=False),
    default="ollama",
    help="LLM provider",
)
@click.option(
    "--model",
    default=None,
    help="Model name (default: provider default)",
)
@click.option(
    "--db-path",
    type=click.Path(exists=True),
    default="./genglossary.db",
    help="Path to database file",
)
def terms_regenerate(input: str, llm_provider: str, model: str | None, db_path: str) -> None:
    """用語を再生成（既存の用語を削除して新規抽出）.

    Example:
        genglossary db terms regenerate --input ./target_docs
    """
    llm_client = _initialize_llm_client(llm_provider, model)

    # Load documents from input directory
    loader = DocumentLoader()
    documents = loader.load_directory(input)

    if not documents:
        console.print(f"[yellow]ドキュメントが見つかりません: {input}[/yellow]")
        return

    console.print(f"[dim]{len(documents)} 件のドキュメントを読み込みました[/dim]")

    # Extract terms and save to database
    # Open connection early to pass excluded_term_repo to TermExtractor
    with _db_operation(db_path) as conn:
        # Extract terms with categories
        extractor = TermExtractor(llm_client=llm_client, excluded_term_repo=conn)
        console.print("[dim]用語を抽出中（カテゴリ付き）...[/dim]")
        classified_terms = extractor.extract_terms(documents, return_categories=True)
        console.print(f"[dim]{len(classified_terms)} 個の用語を抽出しました（カテゴリ付き）[/dim]")

        # Save to database with categories
        with transaction(conn):
            delete_all_terms(conn)
            # Type is list[ClassifiedTerm] when return_categories=True
            for term in classified_terms:  # type: ignore[union-attr]
                create_term(
                    conn,
                    term.term,  # type: ignore[union-attr]
                    category=term.category.value,  # type: ignore[union-attr]
                )
        console.print(f"[green]✓[/green] {len(classified_terms)}件の用語を保存しました（カテゴリ付き）")


@db.group()
def provisional() -> None:
    """暫定用語集の管理コマンド."""
    pass


@provisional.command("list")
@click.option(
    "--db-path",
    type=click.Path(exists=True),
    default="./genglossary.db",
    help="Path to database file",
)
def provisional_list(db_path: str) -> None:
    """暫定用語集一覧を表示.

    Example:
        genglossary db provisional list
    """
    with _db_operation(db_path) as conn:
        term_list = list_all_provisional(conn)

    if not term_list:
        console.print("[yellow]暫定用語がありません[/yellow]")
        return

    table = _create_glossary_term_table(term_list, "暫定用語集")
    console.print(table)


@provisional.command("show")
@click.argument("term_id", type=int)
@click.option(
    "--db-path",
    type=click.Path(exists=True),
    default="./genglossary.db",
    help="Path to database file",
)
def provisional_show(term_id: int, db_path: str) -> None:
    """指定されたterm_idの詳細を表示.

    Example:
        genglossary db provisional show 1
    """
    with _db_operation(db_path) as conn:
        term = get_provisional_term(conn, term_id)

    if term is None:
        console.print(f"[red]Provisional Term ID {term_id} が見つかりません[/red]")
        raise click.Abort()

    _display_glossary_term_details(term, "Provisional")


@provisional.command("update")
@click.argument("term_id", type=int)
@click.option(
    "--definition",
    type=str,
    required=True,
    help="New definition",
)
@click.option(
    "--confidence",
    type=float,
    required=True,
    help="New confidence score (0.0-1.0)",
)
@click.option(
    "--db-path",
    type=click.Path(exists=True),
    default="./genglossary.db",
    help="Path to database file",
)
def provisional_update(term_id: int, definition: str, confidence: float, db_path: str) -> None:
    """暫定用語を更新.

    Example:
        genglossary db provisional update 1 --definition "新しい定義" --confidence 0.95
    """
    with _db_operation(db_path) as conn:
        with transaction(conn):
            update_provisional_term(conn, term_id, definition, confidence)
    console.print(f"[green]✓[/green] Provisional Term #{term_id} を更新しました")


@provisional.command("regenerate")
@click.option(
    "--llm-provider",
    type=click.Choice(["ollama", "openai"], case_sensitive=False),
    default="ollama",
    help="LLM provider",
)
@click.option(
    "--model",
    default=None,
    help="Model name (default: provider default)",
)
@click.option(
    "--db-path",
    type=click.Path(exists=True),
    default="./genglossary.db",
    help="Path to database file",
)
def provisional_regenerate(llm_provider: str, model: str | None, db_path: str) -> None:
    """暫定用語集を再生成（抽出用語とドキュメントから生成）.

    Example:
        genglossary db provisional regenerate
    """
    llm_client = _initialize_llm_client(llm_provider, model)

    with _db_operation(db_path) as conn:
        # Validate and load prerequisites
        data = _validate_prerequisites(
            conn,
            [
                (list_all_terms, "抽出用語がありません。先にterms regenerateを実行してください。"),
                (list_all_documents, "ドキュメントがありません。先にterms regenerateを実行してください。"),
            ],
        )
        if data is None:
            return
        term_rows, doc_rows = data

        # Reconstruct ClassifiedTerm objects from database
        from genglossary.models.term import ClassifiedTerm, TermCategory

        # If category is NULL, treat as common_noun (will be skipped)
        classified_terms = [
            ClassifiedTerm(
                term=row["term_text"],
                category=TermCategory(row["category"] or "common_noun"),
            )
            for row in term_rows
        ]

        documents = _reconstruct_documents_from_db(doc_rows)

        if not documents:
            console.print("[yellow]ドキュメントが読み込めませんでした[/yellow]")
            return

        console.print(
            f"[dim]{len(classified_terms)} 個の用語（カテゴリ付き）、{len(documents)} 件のドキュメントを読み込みました[/dim]"
        )

        # Generate provisional glossary
        generator = GlossaryGenerator(llm_client=llm_client)
        console.print("[dim]用語集を生成中...[/dim]")
        glossary = generator.generate(classified_terms, documents)
        console.print(f"[dim]{len(glossary.terms)} 個の用語定義を生成しました[/dim]")

        # Save to database
        count = _save_glossary_terms(conn, glossary, delete_all_provisional, create_provisional_term)
        console.print(f"[green]✓[/green] {count}件の暫定用語を保存しました")


@db.group()
def refined() -> None:
    """最終用語集の管理コマンド."""
    pass


@refined.command("list")
@click.option(
    "--db-path",
    type=click.Path(exists=True),
    default="./genglossary.db",
    help="Path to database file",
)
def refined_list(db_path: str) -> None:
    """最終用語集一覧を表示.

    Example:
        genglossary db refined list
    """
    with _db_operation(db_path) as conn:
        term_list = list_all_refined(conn)

    if not term_list:
        console.print("[yellow]最終用語がありません[/yellow]")
        return

    table = _create_glossary_term_table(term_list, "最終用語集")
    console.print(table)


@refined.command("show")
@click.argument("term_id", type=int)
@click.option(
    "--db-path",
    type=click.Path(exists=True),
    default="./genglossary.db",
    help="Path to database file",
)
def refined_show(term_id: int, db_path: str) -> None:
    """指定されたterm_idの詳細を表示.

    Example:
        genglossary db refined show 1
    """
    with _db_operation(db_path) as conn:
        term = get_refined_term(conn, term_id)

    if term is None:
        console.print(f"[red]Refined Term ID {term_id} が見つかりません[/red]")
        raise click.Abort()

    _display_glossary_term_details(term, "Refined")


@refined.command("update")
@click.argument("term_id", type=int)
@click.option(
    "--definition",
    type=str,
    required=True,
    help="New definition",
)
@click.option(
    "--confidence",
    type=float,
    required=True,
    help="New confidence score (0.0-1.0)",
)
@click.option(
    "--db-path",
    type=click.Path(exists=True),
    default="./genglossary.db",
    help="Path to database file",
)
def refined_update(term_id: int, definition: str, confidence: float, db_path: str) -> None:
    """最終用語を更新.

    Example:
        genglossary db refined update 1 --definition "新しい定義" --confidence 0.98
    """
    with _db_operation(db_path) as conn:
        with transaction(conn):
            update_refined_term(conn, term_id, definition, confidence)
    console.print(f"[green]✓[/green] Refined Term #{term_id} を更新しました")


@refined.command("export-md")
@click.option(
    "--output",
    type=click.Path(),
    required=True,
    help="Output Markdown file path",
)
@click.option(
    "--db-path",
    type=click.Path(exists=True),
    default="./genglossary.db",
    help="Path to database file",
)
def refined_export_md(output: str, db_path: str) -> None:
    """最終用語集をMarkdown形式でエクスポート.

    Example:
        genglossary db refined export-md --output ./glossary.md
    """
    with _db_operation(db_path) as conn:
        term_list = list_all_refined(conn)

    if not term_list:
        console.print("[yellow]エクスポートする用語がありません[/yellow]")
        return

    # Generate Markdown
    md_lines = ["# 用語集\n"]
    for term in term_list:
        md_lines.append(f"## {term['term_name']}\n")
        md_lines.append(f"**定義**: {term['definition']}\n")
        md_lines.append(f"**信頼度**: {term['confidence']:.2f}\n")

        if term["occurrences"]:
            md_lines.append("\n**出現箇所**:\n")
            for occ in term["occurrences"]:
                md_lines.append(f"- {occ.document_path}:{occ.line_number}\n")

        md_lines.append("\n---\n\n")

    # Write to file
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("".join(md_lines), encoding="utf-8")

    console.print(f"[green]✓[/green] {len(term_list)}件の用語を {output} にエクスポートしました")


@refined.command("regenerate")
@click.option(
    "--llm-provider",
    type=click.Choice(["ollama", "openai"], case_sensitive=False),
    default="ollama",
    help="LLM provider",
)
@click.option(
    "--model",
    default=None,
    help="Model name (default: provider default)",
)
@click.option(
    "--db-path",
    type=click.Path(exists=True),
    default="./genglossary.db",
    help="Path to database file",
)
def refined_regenerate(llm_provider: str, model: str | None, db_path: str) -> None:
    """最終用語集を再生成（暫定用語集と問題から改善）.

    Example:
        genglossary db refined regenerate
    """
    llm_client = _initialize_llm_client(llm_provider, model)

    with _db_operation(db_path) as conn:
        # Validate and load prerequisites
        data = _validate_prerequisites(
            conn,
            [
                (list_all_provisional, "暫定用語がありません。先にprovisional regenerateを実行してください。"),
                (list_all_issues, "精査結果がありません。先にissues regenerateを実行してください。"),
                (list_all_documents, "ドキュメントがありません"),
            ],
        )
        if data is None:
            return
        provisional_rows, issue_rows, doc_rows = data

        # Reconstruct objects from database
        glossary = _reconstruct_glossary_from_rows(provisional_rows)
        issues = _reconstruct_issues_from_rows(issue_rows)
        documents = _reconstruct_documents_from_db(doc_rows)

        if not documents:
            console.print("[yellow]ドキュメントが読み込めませんでした[/yellow]")
            return

        console.print(f"[dim]{len(glossary.terms)} 個の暫定用語、{len(issues)} 個の問題、{len(documents)} 件のドキュメントを読み込みました[/dim]")

        # Refine glossary
        refiner = GlossaryRefiner(llm_client=llm_client)
        console.print("[dim]用語集を改善中...[/dim]")
        refined_glossary = refiner.refine(glossary, issues, documents)
        console.print(f"[dim]{len(refined_glossary.terms)} 個の最終用語を生成しました[/dim]")

        # Save to database
        count = _save_glossary_terms(conn, refined_glossary, delete_all_refined, create_refined_term)
        console.print(f"[green]✓[/green] {count}件の最終用語を保存しました")


@db.group()
def issues() -> None:
    """精査結果の管理コマンド."""
    pass


@issues.command("list")
@click.option(
    "--db-path",
    type=click.Path(exists=True),
    default="./genglossary.db",
    help="Path to database file",
)
def issues_list(db_path: str) -> None:
    """精査結果の一覧を表示.

    Example:
        genglossary db issues list
    """
    with _db_operation(db_path) as conn:
        issue_list = list_all_issues(conn)

    if not issue_list:
        console.print("[yellow]精査結果がありません[/yellow]")
        return

    # Create table
    table = Table(title="精査結果")
    table.add_column("ID", style="cyan")
    table.add_column("用語", style="magenta")
    table.add_column("問題種別", style="yellow")
    table.add_column("説明", style="white")

    for issue in issue_list:
        description = issue["description"]
        truncated_desc = description[:50] + "..." if len(description) > 50 else description
        table.add_row(
            str(issue["id"]),
            issue["term_name"],
            issue["issue_type"],
            truncated_desc,
        )

    console.print(table)


@issues.command("regenerate")
@click.option(
    "--llm-provider",
    type=click.Choice(["ollama", "openai"], case_sensitive=False),
    default="ollama",
    help="LLM provider",
)
@click.option(
    "--model",
    default=None,
    help="Model name (default: provider default)",
)
@click.option(
    "--db-path",
    type=click.Path(exists=True),
    default="./genglossary.db",
    help="Path to database file",
)
def issues_regenerate(llm_provider: str, model: str | None, db_path: str) -> None:
    """精査結果を再生成（暫定用語集を精査）.

    Example:
        genglossary db issues regenerate
    """
    llm_client = _initialize_llm_client(llm_provider, model)

    with _db_operation(db_path) as conn:
        # Validate and load prerequisites
        data = _validate_prerequisites(
            conn,
            [
                (list_all_provisional, "暫定用語がありません。先にprovisional regenerateを実行してください。"),
            ],
        )
        if data is None:
            return
        (provisional_rows,) = data

        # Reconstruct Glossary object
        glossary = _reconstruct_glossary_from_rows(provisional_rows)
        console.print(f"[dim]{len(glossary.terms)} 個の暫定用語を読み込みました[/dim]")

        # Review glossary
        reviewer = GlossaryReviewer(llm_client=llm_client)
        console.print("[dim]用語集を精査中...[/dim]")
        issues = reviewer.review(glossary)
        # Handle None return (cancellation case - should not happen in CLI)
        if issues is None:
            issues = []
        console.print(f"[dim]{len(issues)} 個の問題を検出しました[/dim]")

        # Save issues to database
        count = _save_issues(conn, issues)
        console.print(f"[green]✓[/green] {count}件の問題を保存しました")
