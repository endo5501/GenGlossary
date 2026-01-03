"""Command-line interface for GenGlossary."""

import sys
from datetime import datetime
from pathlib import Path

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from genglossary.document_loader import DocumentLoader
from genglossary.glossary_generator import GlossaryGenerator
from genglossary.glossary_refiner import GlossaryRefiner
from genglossary.glossary_reviewer import GlossaryReviewer
from genglossary.llm.ollama_client import OllamaClient
from genglossary.output.markdown_writer import MarkdownWriter
from genglossary.term_extractor import TermExtractor

console = Console()


def generate_glossary(
    input_dir: str, output_file: str, model: str, verbose: bool
) -> None:
    """Generate glossary from documents.

    Args:
        input_dir: Input directory containing documents.
        output_file: Output file path for the glossary.
        model: Ollama model to use.
        verbose: Whether to show verbose output.
    """
    # Initialize LLM client
    # Use longer timeout for large glossaries (reviews can take time)
    llm_client = OllamaClient(model=model, timeout=180.0)

    # Check Ollama availability
    if not llm_client.is_available():
        raise RuntimeError(
            "Ollamaサーバーに接続できません。\n"
            "ollama serve でサーバーを起動してください。"
        )

    if verbose:
        console.print(f"[dim]入力ディレクトリ: {input_dir}[/dim]")
        console.print(f"[dim]出力ファイル: {output_file}[/dim]")
        console.print(f"[dim]モデル: {model}[/dim]")

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
    if verbose:
        console.print("[dim]用語を抽出中...[/dim]")
    extractor = TermExtractor(llm_client=llm_client)
    terms = extractor.extract_terms(documents)

    if verbose:
        console.print(f"[dim]  → {len(terms)} 個の用語を抽出しました[/dim]")

    # 3. Generate glossary
    if verbose:
        console.print("[dim]用語集を生成中...[/dim]")
    generator = GlossaryGenerator(llm_client=llm_client)
    glossary = generator.generate(terms, documents)

    # 4. Review glossary
    if verbose:
        console.print("[dim]用語集を精査中...[/dim]")
    reviewer = GlossaryReviewer(llm_client=llm_client)
    issues = reviewer.review(glossary)

    if verbose:
        console.print(f"[dim]  → {len(issues)} 個の問題を検出しました[/dim]")

    # 5. Refine glossary
    if issues:
        if verbose:
            console.print("[dim]用語集を改善中...[/dim]")
        refiner = GlossaryRefiner(llm_client=llm_client)
        glossary = refiner.refine(glossary, issues, documents)

    # Add metadata
    glossary.metadata["generated_at"] = datetime.now().isoformat()
    glossary.metadata["document_count"] = len(documents)
    glossary.metadata["model"] = model

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
    "--model",
    "-m",
    default="dengcao/Qwen3-30B-A3B-Instruct-2507:latest",
    help="使用するOllamaモデル名",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="詳細ログを表示",
)
def generate(
    input_dir: Path, output_file: Path, model: str, verbose: bool
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

        console.print("[bold green]GenGlossary[/bold green]")
        console.print(f"入力: {input_dir}")
        console.print(f"出力: {output_file}")
        console.print(f"モデル: {model}\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("用語集を生成中...", total=None)

            # Call the main generation function
            generate_glossary(
                str(input_dir), str(output_file), model, verbose
            )

            progress.update(task, completed=True)

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
    "--model",
    "-m",
    default="dengcao/Qwen3-30B-A3B-Instruct-2507:latest",
    help="使用するOllamaモデル名",
)
def analyze_terms(input_dir: Path, model: str) -> None:
    """用語抽出の中間結果を分析・表示します。

    SudachiPyによる固有名詞抽出とLLMによる用語判定の結果を表示し、
    用語抽出の品質を確認するためのコマンドです。
    """
    try:
        console.print("[bold green]=== 用語抽出分析 ===[/bold green]\n")

        # Initialize LLM client
        llm_client = OllamaClient(model=model, timeout=180.0)

        if not llm_client.is_available():
            console.print(
                "[red]Ollamaサーバーに接続できません。\n"
                "ollama serve でサーバーを起動してください。[/red]"
            )
            sys.exit(1)

        # Load documents
        console.print(f"[dim]入力: {input_dir}[/dim]")
        loader = DocumentLoader()
        documents = loader.load_directory(str(input_dir))

        if not documents:
            console.print(f"[red]ドキュメントが見つかりません: {input_dir}[/red]")
            sys.exit(1)

        console.print(f"[dim]ファイル数: {len(documents)}[/dim]")
        console.print(f"[dim]モデル: {model}[/dim]\n")

        # Analyze extraction
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("用語を分析中...", total=None)

            extractor = TermExtractor(llm_client=llm_client)
            analysis = extractor.analyze_extraction(documents)

            progress.update(task, completed=True)

        # Display results
        console.print(
            f"\n[bold cyan]■ SudachiPy抽出候補[/bold cyan] "
            f"({len(analysis.sudachi_candidates)}件)"
        )
        if analysis.sudachi_candidates:
            candidates_str = ", ".join(analysis.sudachi_candidates)
            console.print(f"  {candidates_str}")
        else:
            console.print("  [dim](なし)[/dim]")

        console.print(
            f"\n[bold green]■ LLM承認用語[/bold green] "
            f"({len(analysis.llm_approved)}件)"
        )
        if analysis.llm_approved:
            approved_str = ", ".join(analysis.llm_approved)
            console.print(f"  {approved_str}")
        else:
            console.print("  [dim](なし)[/dim]")

        console.print(
            f"\n[bold yellow]■ LLM除外用語[/bold yellow] "
            f"({len(analysis.llm_rejected)}件)"
        )
        if analysis.llm_rejected:
            rejected_str = ", ".join(analysis.llm_rejected)
            console.print(f"  {rejected_str}")
        else:
            console.print("  [dim](なし)[/dim]")

        # Statistics
        console.print("\n[bold]■ 統計[/bold]")
        total = len(analysis.sudachi_candidates)
        approved = len(analysis.llm_approved)
        if total > 0:
            rate = (approved / total) * 100
            console.print(f"  候補数: {total}")
            console.print(f"  承認率: {rate:.1f}% ({approved}/{total})")
        else:
            console.print("  候補数: 0")

    except KeyboardInterrupt:
        console.print("\n[yellow]処理を中断しました[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[red]エラーが発生しました: {e}[/red]")
        console.print_exception()
        sys.exit(1)


if __name__ == "__main__":
    main()
