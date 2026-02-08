"""API server commands for GenGlossary CLI."""

import os

import click
import uvicorn
from rich.console import Console

console = Console()


@click.group()
def api() -> None:
    """API server commands.

    FastAPIバックエンドサーバーの起動・管理を行います。
    """
    pass


@api.command()
@click.option(
    "--host",
    default="127.0.0.1",
    help="Bind host (default: 127.0.0.1)",
    show_default=True,
)
@click.option(
    "--port",
    default=8000,
    help="Bind port (default: 8000)",
    show_default=True,
)
@click.option(
    "--reload",
    is_flag=True,
    help="Enable auto-reload on code changes (development)",
)
@click.option(
    "--llm-debug",
    is_flag=True,
    help="Enable LLM debug logging (log prompts and responses to files)",
)
def serve(host: str, port: int, reload: bool, llm_debug: bool) -> None:
    """Start FastAPI server.

    FastAPIサーバーを起動します。

    Examples:
        genglossary api serve
        genglossary api serve --host 0.0.0.0 --port 3000
        genglossary api serve --reload  # Development mode
        genglossary api serve --llm-debug  # Enable LLM debug logging
    """
    if llm_debug:
        os.environ["LLM_DEBUG"] = "true"
        console.print("[yellow]LLM debug logging enabled[/yellow]")

    console.print(f"[green]Starting GenGlossary API server on {host}:{port}[/green]")
    if reload:
        console.print("[yellow]Auto-reload enabled (development mode)[/yellow]")

    uvicorn.run(
        "genglossary.api.app:create_app",
        host=host,
        port=port,
        reload=reload,
        factory=True,
        log_level="info",
    )
