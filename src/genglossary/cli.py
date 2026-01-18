"""Command-line interface for GenGlossary."""

import sys
from datetime import datetime
from pathlib import Path
from typing import Callable

import click
from rich.console import Console

from genglossary.cli_db import db
from genglossary.config import Config
from genglossary.document_loader import DocumentLoader
from genglossary.glossary_generator import GlossaryGenerator
from genglossary.glossary_refiner import GlossaryRefiner
from genglossary.glossary_reviewer import GlossaryReviewer
from genglossary.llm.base import BaseLLMClient
from genglossary.llm.ollama_client import OllamaClient
from genglossary.llm.openai_compatible_client import OpenAICompatibleClient
from genglossary.models.document import Document
from genglossary.models.glossary import Glossary
from genglossary.progress import progress_task
from genglossary.output.markdown_writer import MarkdownWriter
from genglossary.term_extractor import TermExtractor, TermExtractionAnalysis

console = Console()


def create_llm_client(
    provider: str,
    model: str | None = None,
    openai_base_url: str | None = None,
    timeout: float = 180.0,
) -> BaseLLMClient:
    """Create LLM client based on provider.

    Args:
        provider: LLM provider ("ollama" or "openai").
        model: Model name (provider-specific default if None).
        openai_base_url: Base URL for OpenAI-compatible API (optional).
        timeout: Request timeout in seconds.

    Returns:
        Configured LLM client instance.

    Raises:
        ValueError: If provider is unknown.
    """
    if provider == "ollama":
        return OllamaClient(
            model=model or "dengcao/Qwen3-30B-A3B-Instruct-2507:latest",
            timeout=timeout,
        )

    if provider == "openai":
        config = Config()
        return OpenAICompatibleClient(
            base_url=openai_base_url or config.openai_base_url,
            api_key=config.openai_api_key,
            model=model or config.openai_model,
            timeout=timeout,
            api_version=config.azure_openai_api_version,
        )

    raise ValueError(f"Unknown provider: {provider}. Must be 'ollama' or 'openai'.")


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
    verbose: bool
) -> None:
    """Generate glossary from documents.

    Args:
        input_dir: Input directory containing documents.
        output_file: Output file path for the glossary.
        provider: LLM provider ("ollama" or "openai").
        model: Model name to use (None for provider default).
        openai_base_url: Base URL for OpenAI-compatible API (optional).
        verbose: Whether to show verbose output.
    """
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
    if model is None:
        config = Config()
        actual_model = (
            config.ollama_model if provider == "ollama" else config.openai_model
        )
    else:
        actual_model = model

    if verbose:
        console.print(f"[dim]入力ディレクトリ: {input_dir}[/dim]")
        console.print(f"[dim]出力ファイル: {output_file}[/dim]")
        console.print(f"[dim]モデル: {actual_model}[/dim]")

    # 1. Load documents
    if verbose:
        console.print("[dim]ドキュメントを読み込み中...[/dim]")
    loader = DocumentLoader()
    documents = loader.load_directory(input_dir)

    if not documents:
        raise ValueError(f"ドキュメントが見つかりません: {input_dir}")

    if verbose:
        console.print(f"[dim]  → {len(documents)} ファイルを読み込みました[/dim]")

    # 2. Extract terms
    extractor = TermExtractor(llm_client=llm_client)
    if verbose:
        with progress_task(console, "用語を分類中...", total=None) as update:
            terms = extractor.extract_terms(documents, progress_callback=update)
        console.print(f"[dim]  → {len(terms)} 個の用語を抽出しました[/dim]")
    else:
        terms = extractor.extract_terms(documents)

    # 3. Generate glossary
    generator = GlossaryGenerator(llm_client=llm_client)
    if verbose:
        with progress_task(console, "定義を生成中...", total=len(terms)) as update:
            glossary = generator.generate(terms, documents, progress_callback=update)
    else:
        glossary = generator.generate(terms, documents)

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

    # Add metadata
    _add_glossary_metadata(glossary, actual_model, len(documents))

    # 6. Write output
    if verbose:
        console.print("[dim]用語集を出力中...[/dim]")
    writer = MarkdownWriter()
    writer.write(glossary, output_file)

    if verbose:
        console.print(f"[dim]  → {glossary.term_count} 個の用語を出力しました[/dim]")


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
        if model is None:
            config = Config()
            display_model = (
                config.ollama_model if llm_provider == "ollama" else config.openai_model
            )
        else:
            display_model = model

        console.print("[bold green]GenGlossary[/bold green]")
        console.print(f"入力: {input_dir}")
        console.print(f"出力: {output_file}")
        console.print(f"プロバイダー: {llm_provider}")
        console.print(f"モデル: {display_model}\n")

        with progress_task(console, "用語集を生成中...", use_spinner_only=True):
            # Call the main generation function
            generate_glossary(
                str(input_dir),
                str(output_file),
                llm_provider,
                model,
                openai_base_url,
                verbose
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
        if model is None:
            config = Config()
            display_model = (
                config.ollama_model if llm_provider == "ollama" else config.openai_model
            )
        else:
            display_model = model

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
main.add_command(db)


if __name__ == "__main__":
    main()
