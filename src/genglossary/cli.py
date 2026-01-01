"""Command-line interface for GenGlossary."""

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


def generate_glossary(
    input_dir: str, output_file: str, model: str, verbose: bool
) -> None:
    """Generate glossary from documents.

    This is a placeholder function that will integrate all components.

    Args:
        input_dir: Input directory containing documents.
        output_file: Output file path for the glossary.
        model: Ollama model to use.
        verbose: Whether to show verbose output.
    """
    # TODO: Integrate with actual glossary generation pipeline
    # For now, this is a placeholder implementation
    if verbose:
        console.print(f"[dim]入力ディレクトリ: {input_dir}[/dim]")
        console.print(f"[dim]出力ファイル: {output_file}[/dim]")
        console.print(f"[dim]モデル: {model}[/dim]")

    console.print("[yellow]用語集生成機能は Phase 5 で統合予定です[/yellow]")


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
    default="llama2",
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


if __name__ == "__main__":
    main()
