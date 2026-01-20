"""Database CLI commands for GenGlossary."""

from pathlib import Path

import click
import sqlite3
from rich.console import Console
from rich.table import Table

from genglossary.db.connection import get_connection
from genglossary.db.models import GlossaryTermRow
from genglossary.db.provisional_repository import (
    get_provisional_term,
    list_all_provisional,
    update_provisional_term,
)
from genglossary.db.refined_repository import (
    get_refined_term,
    list_all_refined,
    update_refined_term,
)
from genglossary.db.metadata_repository import get_metadata
from genglossary.db.issue_repository import list_all_issues
from genglossary.db.schema import initialize_db
from genglossary.db.term_repository import (
    create_term,
    delete_term,
    get_term,
    list_all_terms,
    update_term,
)

console = Console()


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
    try:
        db_path = Path(path)

        # Create connection and initialize schema
        conn = get_connection(str(db_path))
        initialize_db(conn)
        conn.close()

        console.print(f"[green]✓[/green] データベースを初期化しました: {db_path}")
        console.print(f"[dim]  親ディレクトリ: {db_path.parent.absolute()}[/dim]")

    except Exception as e:
        console.print(f"[red]エラー: {e}[/red]")
        raise click.Abort()


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
    try:
        conn = get_connection(db_path)
        metadata = get_metadata(conn)
        conn.close()

        if metadata is None:
            console.print("[yellow]メタデータがありません[/yellow]")
            return

        # Display metadata
        console.print("\n[bold]メタデータ[/bold]")
        console.print(f"LLMプロバイダー: {metadata['llm_provider']}")
        console.print(f"LLMモデル: {metadata['llm_model']}")
        console.print(f"作成日時: {metadata['created_at']}")

    except Exception as e:
        console.print(f"[red]エラー: {e}[/red]")
        raise click.Abort()


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
    try:
        conn = get_connection(db_path)
        term_list = list_all_terms(conn)
        conn.close()

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

    except Exception as e:
        console.print(f"[red]エラー: {e}[/red]")
        raise click.Abort()


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
    try:
        conn = get_connection(db_path)
        term = get_term(conn, term_id)
        conn.close()

        if term is None:
            console.print(f"[red]Term ID {term_id} が見つかりません[/red]")
            raise click.Abort()

        # Display term details
        console.print(f"\n[bold]Term #{term['id']}[/bold]")
        console.print(f"用語: {term['term_text']}")
        console.print(f"カテゴリ: {term['category'] or '[dim]なし[/dim]'}")

    except Exception as e:
        console.print(f"[red]エラー: {e}[/red]")
        raise click.Abort()


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
    try:
        conn = get_connection(db_path)
        update_term(conn, term_id, text, category)
        conn.close()

        console.print(f"[green]✓[/green] Term #{term_id} を更新しました")

    except Exception as e:
        console.print(f"[red]エラー: {e}[/red]")
        raise click.Abort()


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
    try:
        conn = get_connection(db_path)
        delete_term(conn, term_id)
        conn.close()

        console.print(f"[green]✓[/green] Term #{term_id} を削除しました")

    except Exception as e:
        console.print(f"[red]エラー: {e}[/red]")
        raise click.Abort()


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
    try:
        # Read terms from file
        with open(file, "r", encoding="utf-8") as f:
            term_texts = [line.strip() for line in f if line.strip()]

        # Import terms
        conn = get_connection(db_path)
        for term_text in term_texts:
            create_term(conn, term_text)
        conn.close()

        console.print(
            f"[green]✓[/green] {len(term_texts)}件の用語をインポートしました"
        )

    except Exception as e:
        console.print(f"[red]エラー: {e}[/red]")
        raise click.Abort()


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
    try:
        conn = get_connection(db_path)
        term_list = list_all_provisional(conn)
        conn.close()

        if not term_list:
            console.print("[yellow]暫定用語がありません[/yellow]")
            return

        table = _create_glossary_term_table(term_list, "暫定用語集")
        console.print(table)

    except Exception as e:
        console.print(f"[red]エラー: {e}[/red]")
        raise click.Abort()


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
    try:
        conn = get_connection(db_path)
        term = get_provisional_term(conn, term_id)
        conn.close()

        if term is None:
            console.print(f"[red]Provisional Term ID {term_id} が見つかりません[/red]")
            raise click.Abort()

        _display_glossary_term_details(term, "Provisional")

    except Exception as e:
        console.print(f"[red]エラー: {e}[/red]")
        raise click.Abort()


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
    try:
        conn = get_connection(db_path)
        update_provisional_term(conn, term_id, definition, confidence)
        conn.close()

        console.print(f"[green]✓[/green] Provisional Term #{term_id} を更新しました")

    except Exception as e:
        console.print(f"[red]エラー: {e}[/red]")
        raise click.Abort()


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
    try:
        conn = get_connection(db_path)
        term_list = list_all_refined(conn)
        conn.close()

        if not term_list:
            console.print("[yellow]最終用語がありません[/yellow]")
            return

        table = _create_glossary_term_table(term_list, "最終用語集")
        console.print(table)

    except Exception as e:
        console.print(f"[red]エラー: {e}[/red]")
        raise click.Abort()


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
    try:
        conn = get_connection(db_path)
        term = get_refined_term(conn, term_id)
        conn.close()

        if term is None:
            console.print(f"[red]Refined Term ID {term_id} が見つかりません[/red]")
            raise click.Abort()

        _display_glossary_term_details(term, "Refined")

    except Exception as e:
        console.print(f"[red]エラー: {e}[/red]")
        raise click.Abort()


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
    try:
        conn = get_connection(db_path)
        update_refined_term(conn, term_id, definition, confidence)
        conn.close()

        console.print(f"[green]✓[/green] Refined Term #{term_id} を更新しました")

    except Exception as e:
        console.print(f"[red]エラー: {e}[/red]")
        raise click.Abort()


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
    try:
        conn = get_connection(db_path)
        term_list = list_all_refined(conn)
        conn.close()

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

    except Exception as e:
        console.print(f"[red]エラー: {e}[/red]")
        raise click.Abort()
