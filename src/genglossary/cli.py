"""Command-line interface for GenGlossary."""

import hashlib
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import click
from rich.console import Console

from genglossary.config import Config
from genglossary.db.connection import get_connection
from genglossary.db.document_repository import create_document
from genglossary.db.issue_repository import create_issue
from genglossary.db.provisional_repository import create_provisional_term
from genglossary.db.refined_repository import create_refined_term
from genglossary.db.metadata_repository import upsert_metadata
from genglossary.db.schema import initialize_db
from genglossary.db.term_repository import create_term
from genglossary.document_loader import DocumentLoader
from genglossary.glossary_generator import GlossaryGenerator
from genglossary.glossary_refiner import GlossaryRefiner
from genglossary.glossary_reviewer import GlossaryReviewer
from genglossary.llm.base import BaseLLMClient
from genglossary.llm.factory import create_llm_client
from genglossary.models.document import Document
from genglossary.models.glossary import Glossary
from genglossary.progress import progress_task
from genglossary.output.markdown_writer import MarkdownWriter
from genglossary.term_extractor import TermExtractor, TermExtractionAnalysis

console = Console()


def _get_actual_model_name(provider: str, model: str | None) -> str:
    """Get the actual model name to use.

    Args:
        provider: LLM provider name.
        model: User-specified model name (None for default).

    Returns:
        str: Actual model name to use.
    """
    if model is not None:
        return model

    config = Config()
    return config.ollama_model if provider == "ollama" else config.openai_model


def _add_glossary_metadata(glossary: Glossary, model: str, document_count: int) -> None:
    """Add metadata to glossary.

    Args:
        glossary: Glossary to update.
        model: Model name used for generation.
        document_count: Number of documents processed.
    """
    glossary.metadata["generated_at"] = datetime.now().isoformat()
    glossary.metadata["document_count"] = document_count
    glossary.metadata["model"] = model


def generate_glossary(
    input_dir: str,
    output_file: str,
    provider: str,
    model: str | None,
    openai_base_url: str | None,
    verbose: bool,
    db_path: str | None = None,
) -> None:
    """Generate glossary from documents.

    Args:
        input_dir: Input directory containing documents.
        output_file: Output file path for the glossary.
        provider: LLM provider ("ollama" or "openai").
        model: Model name to use (None for provider default).
        openai_base_url: Base URL for OpenAI-compatible API (optional).
        verbose: Whether to show verbose output.
        db_path: Path to SQLite database for persistence (optional).
    """
    # Initialize database connection if db_path is provided
    conn = None
    if db_path is not None:
        conn = get_connection(db_path)
        initialize_db(conn)
        if verbose:
            console.print(f"[dim]データベース: {db_path}[/dim]")

    # Initialize LLM client
    # Use longer timeout for large glossaries (reviews can take time)
    llm_client = create_llm_client(
        provider=provider,
        model=model,
        openai_base_url=openai_base_url,
        timeout=180.0,
    )

    # Check service availability
    if not llm_client.is_available():
        if provider == "ollama":
            raise RuntimeError(
                "Ollamaサーバーに接続できません。\n"
                "ollama serve でサーバーを起動してください。"
            )
        else:
            raise RuntimeError(
                f"{provider} APIに接続できません。\n"
                "エンドポイントURLとAPIキーを確認してください。"
            )

    # Determine actual model name for logging and metadata
    actual_model = _get_actual_model_name(provider, model)

    if verbose:
        console.print(f"[dim]入力ディレクトリ: {input_dir}[/dim]")
        console.print(f"[dim]出力ファイル: {output_file}[/dim]")
        console.print(f"[dim]モデル: {actual_model}[/dim]")

    # Save metadata if database is enabled
    if conn is not None:
        upsert_metadata(conn, input_dir, provider, actual_model)
        if verbose:
            console.print(f"[dim]メタデータを保存しました[/dim]")

    try:
        # Process glossary generation with error handling
        _generate_glossary_with_db(
            input_dir=input_dir,
            output_file=output_file,
            llm_client=llm_client,
            actual_model=actual_model,
            documents=None,  # Will be loaded inside
            verbose=verbose,
            conn=conn,
        )
    except Exception as e:
        # Close connection before re-raising
        if conn is not None:
            conn.close()
        raise


def _generate_glossary_with_db(
    input_dir: str,
    output_file: str,
    llm_client: BaseLLMClient,
    actual_model: str,
    documents: list[Document] | None,
    verbose: bool,
    conn: Any | None,
) -> None:
    """Internal function for glossary generation with database support.

    Args:
        input_dir: Input directory path.
        output_file: Output file path.
        llm_client: LLM client instance.
        actual_model: Actual model name being used.
        documents: Pre-loaded documents (None to load from input_dir).
        verbose: Whether to show verbose output.
        conn: Database connection (None if database is disabled).
    """
    # 1. Load documents
    if verbose:
        console.print("[dim]ドキュメントを読み込み中...[/dim]")
    loader = DocumentLoader()
    documents = loader.load_directory(input_dir)

    if not documents:
        raise ValueError(f"ドキュメントが見つかりません: {input_dir}")

    if verbose:
        console.print(f"[dim]  → {len(documents)} ファイルを読み込みました[/dim]")

    # Save documents to database if enabled
    if conn is not None:
        for document in documents:
            # Calculate content hash for deduplication
            content_hash = hashlib.sha256(document.content.encode("utf-8")).hexdigest()
            create_document(conn, document.file_path, content_hash)
        if verbose:
            console.print(f"[dim]  → データベースに {len(documents)} 件のドキュメントを保存[/dim]")

    # 2. Extract terms
    extractor = TermExtractor(llm_client=llm_client)

    # Extract terms with categories if DB is enabled
    return_categories = conn is not None

    # Extract terms with progress display if verbose
    if verbose:
        with progress_task(console, "用語を分類中...", total=None) as update:
            extracted_terms = extractor.extract_terms(
                documents, progress_callback=update, return_categories=return_categories
            )
        category_msg = "（カテゴリ付き）" if return_categories else ""
        console.print(
            f"[dim]  → {len(extracted_terms)} 個の用語を抽出しました{category_msg}[/dim]"
        )
    else:
        extracted_terms = extractor.extract_terms(
            documents, return_categories=return_categories
        )

    # Save extracted terms to database if enabled
    if conn is not None:
        # Type is guaranteed to be list[ClassifiedTerm] when return_categories=True
        for classified_term in extracted_terms:  # type: ignore[union-attr]
            create_term(
                conn,
                classified_term.term,  # type: ignore[union-attr]
                category=classified_term.category.value,  # type: ignore[union-attr]
            )
        if verbose:
            console.print(
                f"[dim]  → データベースに {len(extracted_terms)} 件の抽出語を保存（カテゴリ付き）[/dim]"
            )

    # 3. Generate glossary
    generator = GlossaryGenerator(llm_client=llm_client)
    if verbose:
        with progress_task(
            console, "定義を生成中...", total=len(extracted_terms)
        ) as update:
            glossary = generator.generate(
                extracted_terms, documents, progress_callback=update
            )
    else:
        glossary = generator.generate(extracted_terms, documents)

    # Save provisional glossary to database if enabled
    if conn is not None:
        for term in glossary.terms.values():
            create_provisional_term(
                conn,
                term.name,
                term.definition,
                term.confidence,
                term.occurrences,
            )
        if verbose:
            console.print(f"[dim]  → データベースに {len(glossary.terms)} 件の暫定用語を保存[/dim]")

    # 4. Review glossary
    reviewer = GlossaryReviewer(llm_client=llm_client)
    if verbose:
        with progress_task(console, "精査中...", use_spinner_only=True):
            issues = reviewer.review(glossary)
    else:
        issues = reviewer.review(glossary)

    if verbose:
        console.print(f"[dim]  → {len(issues)} 個の問題を検出しました[/dim]")
        # Display count of terms to be excluded
        exclude_count = sum(1 for issue in issues if issue.should_exclude)
        if exclude_count > 0:
            console.print(f"[dim]  → {exclude_count} 個の用語を除外予定[/dim]")

    # Save issues to database if enabled
    if conn is not None:
        for issue in issues:
            create_issue(
                conn,
                issue.term_name,
                issue.issue_type,
                issue.description,
            )
        if verbose:
            console.print(f"[dim]  → データベースに {len(issues)} 件の問題を保存[/dim]")

    # 5. Refine glossary
    if issues:
        refiner = GlossaryRefiner(llm_client=llm_client)
        if verbose:
            with progress_task(console, "改善中...", total=len(issues)) as update:
                glossary = refiner.refine(glossary, issues, documents, progress_callback=update)
        else:
            glossary = refiner.refine(glossary, issues, documents)

        # Display excluded terms if any
        if verbose and "excluded_terms" in glossary.metadata:
            excluded_terms = glossary.metadata["excluded_terms"]
            console.print(f"[dim]  → {len(excluded_terms)} 個の用語を除外しました[/dim]")
            if excluded_terms:
                for excluded in excluded_terms:
                    reason = excluded.get("reason", "理由不明")
                    console.print(f"[dim]    - {excluded['term_name']}: {reason}[/dim]")

    # Save refined glossary to database if enabled
    if conn is not None:
        for term in glossary.terms.values():
            create_refined_term(
                conn,
                term.name,
                term.definition,
                term.confidence,
                term.occurrences,
            )
        if verbose:
            console.print(f"[dim]  → データベースに {len(glossary.terms)} 件の最終用語を保存[/dim]")

    # Add metadata
    _add_glossary_metadata(glossary, actual_model, len(documents))

    # 6. Write output
    if verbose:
        console.print("[dim]用語集を出力中...[/dim]")
    writer = MarkdownWriter()
    writer.write(glossary, output_file)

    if verbose:
        console.print(f"[dim]  → {glossary.term_count} 個の用語を出力しました[/dim]")

    # Close database connection if enabled
    if conn is not None:
        conn.close()


@click.group()
@click.version_option(version="0.1.0", prog_name="GenGlossary")
def main() -> None:
    """GenGlossary - AI-powered glossary generator from documents.

    ドキュメントから用語集を自動生成するツールです。
    """
    pass


@main.command()
@click.option(
    "--input",
    "-i",
    "input_dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default="./target_docs",
    help="入力ドキュメントのディレクトリ",
)
@click.option(
    "--output",
    "-o",
    "output_file",
    type=click.Path(path_type=Path),
    default="./output/glossary.md",
    help="出力する用語集ファイルのパス",
)
@click.option(
    "--llm-provider",
    type=click.Choice(["ollama", "openai"], case_sensitive=False),
    default="ollama",
    help="LLMプロバイダー: ollama または openai（OpenAI互換API）",
)
@click.option(
    "--model",
    "-m",
    default=None,
    help="使用するモデル名（省略時はプロバイダーごとのデフォルト値）",
)
@click.option(
    "--openai-base-url",
    default=None,
    help="OpenAI互換APIのベースURL（--llm-provider=openai時のみ有効）",
)
@click.option(
    "--db-path",
    type=click.Path(path_type=Path),
    default="./genglossary.db",
    help="SQLiteデータベースのパス（デフォルト: genglossary.db）",
)
@click.option(
    "--no-db",
    is_flag=True,
    help="データベース保存をスキップ",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="詳細ログを表示",
)
def generate(
    input_dir: Path,
    output_file: Path,
    llm_provider: str,
    model: str | None,
    openai_base_url: str | None,
    db_path: Path | None,
    no_db: bool,
    verbose: bool
) -> None:
    """ドキュメントから用語集を生成します。

    指定されたディレクトリ内のドキュメントを解析し、
    AIを使って用語集を自動生成します。
    """
    try:
        # Verify input directory exists
        if not input_dir.exists():
            console.print(
                f"[red]エラー: 入力ディレクトリが存在しません: {input_dir}[/red]"
            )
            sys.exit(1)

        # Determine model name for display
        display_model = _get_actual_model_name(llm_provider, model)

        console.print("[bold green]GenGlossary[/bold green]")
        console.print(f"入力: {input_dir}")
        console.print(f"出力: {output_file}")
        console.print(f"プロバイダー: {llm_provider}")
        console.print(f"モデル: {display_model}")
        effective_db_path = None if no_db else db_path

        if effective_db_path is not None:
            console.print(f"データベース: {effective_db_path}")
        console.print()

        with progress_task(console, "用語集を生成中...", use_spinner_only=True):
            # Call the main generation function
            generate_glossary(
                str(input_dir),
                str(output_file),
                llm_provider,
                model,
                openai_base_url,
                verbose,
                db_path=str(effective_db_path) if effective_db_path else None,
            )

        console.print("\n[bold green]✓ 用語集の生成が完了しました[/bold green]")
        console.print(f"出力ファイル: {output_file}")

    except KeyboardInterrupt:
        console.print("\n[yellow]処理を中断しました[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[red]エラーが発生しました: {e}[/red]")
        if verbose:
            console.print_exception()
        sys.exit(1)


def _display_filtering_results(analysis: TermExtractionAnalysis) -> None:
    """Display filtering results section.

    Args:
        analysis: Term extraction analysis results.
    """
    console.print("\n[bold magenta]■ 包含フィルタリング[/bold magenta]")
    pre_count = analysis.pre_filter_candidate_count
    post_count = analysis.post_filter_candidate_count
    filtered_count = pre_count - post_count
    console.print(f"  フィルタ前: {pre_count}件")
    console.print(f"  フィルタ後: {post_count}件")
    console.print(f"  除去された重複: {filtered_count}件")
    if pre_count > 0:
        reduction_rate = (filtered_count / pre_count) * 100
        console.print(f"  削減率: {reduction_rate:.1f}%")


def _display_classification_results(analysis: TermExtractionAnalysis) -> None:
    """Display classification results section.

    Args:
        analysis: Term extraction analysis results.
    """
    console.print("\n[bold blue]■ LLM分類結果[/bold blue]")
    if not analysis.classification_results:
        console.print("  [dim](なし)[/dim]")
        return

    category_labels = {
        "person_name": "人名",
        "place_name": "地名",
        "organization": "組織・団体名",
        "title": "役職・称号",
        "technical_term": "技術用語",
        "common_noun": "一般名詞（除外対象）",
    }

    for category, terms in analysis.classification_results.items():
        label = category_labels.get(category, category)
        is_common_noun = category == "common_noun"

        if is_common_noun:
            console.print(f"  [dim]{label}: {len(terms)}件[/dim]")
        else:
            console.print(f"  {label}: {len(terms)}件")

        if terms:
            terms_str = ", ".join(terms)
            if is_common_noun:
                console.print(f"    [dim]{terms_str}[/dim]")
            else:
                console.print(f"    {terms_str}")


def _display_term_lists(analysis: TermExtractionAnalysis) -> None:
    """Display term lists (candidates, approved, rejected).

    Args:
        analysis: Term extraction analysis results.
    """
    # SudachiPy candidates
    console.print(
        f"\n[bold cyan]■ SudachiPy抽出候補[/bold cyan] "
        f"({len(analysis.sudachi_candidates)}件)"
    )
    if analysis.sudachi_candidates:
        candidates_str = ", ".join(analysis.sudachi_candidates)
        console.print(f"  {candidates_str}")
    else:
        console.print("  [dim](なし)[/dim]")

    # LLM approved terms
    console.print(
        f"\n[bold green]■ LLM承認用語[/bold green] "
        f"({len(analysis.llm_approved)}件)"
    )
    if analysis.llm_approved:
        approved_str = ", ".join(analysis.llm_approved)
        console.print(f"  {approved_str}")
    else:
        console.print("  [dim](なし)[/dim]")

    # LLM rejected terms
    console.print(
        f"\n[bold yellow]■ LLM除外用語[/bold yellow] "
        f"({len(analysis.llm_rejected)}件)"
    )
    if analysis.llm_rejected:
        rejected_str = ", ".join(analysis.llm_rejected)
        console.print(f"  {rejected_str}")
    else:
        console.print("  [dim](なし)[/dim]")


def _display_statistics(analysis: TermExtractionAnalysis) -> None:
    """Display statistics section.

    Args:
        analysis: Term extraction analysis results.
    """
    console.print("\n[bold]■ 統計[/bold]")
    total = len(analysis.sudachi_candidates)
    approved = len(analysis.llm_approved)

    if total > 0:
        rate = (approved / total) * 100
        console.print(f"  候補数: {total}")
        console.print(f"  承認率: {rate:.1f}% ({approved}/{total})")
    else:
        console.print("  候補数: 0")


def _run_term_extraction_analysis(
    documents: list[Document],
    extractor: TermExtractor,
    batch_size: int,
) -> TermExtractionAnalysis:
    """Run term extraction analysis with progress display.

    Args:
        documents: Documents to analyze.
        extractor: Term extractor instance.
        batch_size: Batch size for LLM classification.

    Returns:
        Term extraction analysis results.
    """
    # Extract candidates and show initial info
    console.print("[dim]候補抽出中...[/dim]")
    all_candidates = extractor.get_candidates(documents, filter_contained=True)

    total_candidates = len(all_candidates)
    total_batches = (
        (total_candidates + batch_size - 1) // batch_size if total_candidates > 0 else 0
    )
    console.print(f"[dim]候補数: {total_candidates}件 → {total_batches}バッチで分類[/dim]\n")

    # Run analysis with progress bar
    with progress_task(console, "LLM分類中...", total=total_batches) as update:
        analysis = extractor.analyze_extraction(
            documents,
            progress_callback=update,
            batch_size=batch_size,
        )

    return analysis


@main.command(name="analyze-terms")
@click.option(
    "--input",
    "-i",
    "input_dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    required=True,
    help="入力ドキュメントのディレクトリ",
)
@click.option(
    "--llm-provider",
    type=click.Choice(["ollama", "openai"], case_sensitive=False),
    default="ollama",
    help="LLMプロバイダー: ollama または openai（OpenAI互換API）",
)
@click.option(
    "--model",
    "-m",
    default=None,
    help="使用するモデル名（省略時はプロバイダーごとのデフォルト値）",
)
@click.option(
    "--openai-base-url",
    default=None,
    help="OpenAI互換APIのベースURL（--llm-provider=openai時のみ有効）",
)
@click.option(
    "--batch-size",
    "-b",
    default=10,
    type=int,
    help="LLM分類のバッチサイズ（デフォルト: 10）",
)
def analyze_terms(
    input_dir: Path,
    llm_provider: str,
    model: str | None,
    openai_base_url: str | None,
    batch_size: int
) -> None:
    """用語抽出の中間結果を分析・表示します。

    SudachiPyによる固有名詞抽出とLLMによる用語判定の結果を表示し、
    用語抽出の品質を確認するためのコマンドです。
    """
    try:
        console.print("[bold green]=== 用語抽出分析 ===[/bold green]\n")

        # Initialize LLM client
        llm_client = create_llm_client(
            provider=llm_provider,
            model=model,
            openai_base_url=openai_base_url,
            timeout=180.0,
        )

        if not llm_client.is_available():
            if llm_provider == "ollama":
                console.print(
                    "[red]Ollamaサーバーに接続できません。\n"
                    "ollama serve でサーバーを起動してください。[/red]"
                )
            else:
                console.print(
                    f"[red]{llm_provider} APIに接続できません。\n"
                    "エンドポイントURLとAPIキーを確認してください。[/red]"
                )
            sys.exit(1)

        # Determine model name for display
        display_model = _get_actual_model_name(llm_provider, model)

        # Load documents
        console.print(f"[dim]入力: {input_dir}[/dim]")
        loader = DocumentLoader()
        documents = loader.load_directory(str(input_dir))

        if not documents:
            console.print(f"[red]ドキュメントが見つかりません: {input_dir}[/red]")
            sys.exit(1)

        console.print(f"[dim]ファイル数: {len(documents)}[/dim]")
        console.print(f"[dim]プロバイダー: {llm_provider}[/dim]")
        console.print(f"[dim]モデル: {display_model}[/dim]")
        console.print(f"[dim]バッチサイズ: {batch_size}[/dim]\n")

        # Run analysis
        extractor = TermExtractor(llm_client=llm_client)
        analysis = _run_term_extraction_analysis(documents, extractor, batch_size)

        # Display results
        _display_filtering_results(analysis)
        _display_term_lists(analysis)
        _display_classification_results(analysis)
        _display_statistics(analysis)

    except KeyboardInterrupt:
        console.print("\n[yellow]処理を中断しました[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[red]エラーが発生しました: {e}[/red]")
        console.print_exception()
        sys.exit(1)


# Register db subcommand group
from genglossary.cli_db import db

main.add_command(db)

# Register api subcommand group
from genglossary.cli_api import api

main.add_command(api)


if __name__ == "__main__":
    main()
