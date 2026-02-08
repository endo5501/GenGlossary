"""Project CLI commands for GenGlossary."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator
from uuid import uuid4

import click
from rich.console import Console
from rich.table import Table

from genglossary.db.connection import transaction
from genglossary.db.project_repository import (
    clone_project,
    create_project,
    delete_project,
    get_project_by_name,
    list_projects,
)
from genglossary.db.registry_connection import (
    get_default_registry_path,
    get_registry_connection,
)
from genglossary.db.registry_schema import initialize_registry
from genglossary.models.project import ProjectStatus

console = Console()



def _get_projects_dir(registry: Path | None) -> Path:
    """Get projects directory path based on registry location.

    Args:
        registry: Optional path to registry database.

    Returns:
        Path to projects directory.
    """
    if registry:
        base_dir = registry.parent
    else:
        base_dir = get_default_registry_path().parent

    return base_dir / "projects"


def _get_project_db_path(registry: Path | None, project_name: str) -> Path:
    """Get project database path and ensure parent directory exists.

    Args:
        registry: Optional path to registry database.
        project_name: Name of the project.

    Returns:
        Path to project database file (absolute path).
    """
    projects_dir = _get_projects_dir(registry)
    projects_dir.mkdir(parents=True, exist_ok=True)
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in project_name)
    unique_id = uuid4().hex[:8]
    db_path = projects_dir / f"{safe_name}_{unique_id}.db"
    return db_path.resolve()


@contextmanager
def _registry_connection(
    registry_path: str | None,
) -> Generator[sqlite3.Connection, None, None]:
    """Context manager for registry database connection.

    Args:
        registry_path: Optional path to registry database.

    Yields:
        SQLite connection to registry database.
    """
    if registry_path is None:
        registry_path = str(get_default_registry_path())

    conn = get_registry_connection(registry_path)
    initialize_registry(conn)
    try:
        yield conn
    finally:
        conn.close()


@click.group()
def project():
    """プロジェクト管理コマンド"""
    pass


@project.command()
@click.argument("name")
@click.option(
    "--doc-root",
    required=True,
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="ドキュメントディレクトリのパス",
)
@click.option(
    "--llm-provider",
    default="ollama",
    help="LLMプロバイダー (デフォルト: ollama)",
)
@click.option(
    "--llm-model",
    default="",
    help="LLMモデル名",
)
@click.option(
    "--registry",
    type=click.Path(path_type=Path),
    help="レジストリDBのパス (デフォルト: ~/.genglossary/registry.db)",
)
def init(
    name: str,
    doc_root: Path,
    llm_provider: str,
    llm_model: str,
    registry: Path | None,
):
    """新しいプロジェクトを作成する

    プロジェクトはドキュメントディレクトリと設定をまとめて管理します。
    """
    try:
        with _registry_connection(str(registry) if registry else None) as conn:
            project_db_path = _get_project_db_path(registry, name)

            # Create project
            with transaction(conn):
                project_id = create_project(
                    conn,
                    name=name,
                    doc_root=str(doc_root.absolute()),
                    db_path=str(project_db_path),
                    llm_provider=llm_provider,
                    llm_model=llm_model,
                )

            console.print(f"[green]✓[/green] プロジェクトを作成しました: {name}")
            console.print(f"  ID: {project_id}")
            console.print(f"  ドキュメント: {doc_root}")
            console.print(f"  DB: {project_db_path}")

    except Exception as e:
        console.print(f"[red]エラー: {e}[/red]")
        raise click.Abort()


@project.command()
@click.option(
    "--registry",
    type=click.Path(path_type=Path),
    help="レジストリDBのパス (デフォルト: ~/.genglossary/registry.db)",
)
def list(registry: Path | None):
    """プロジェクト一覧を表示する"""
    try:
        with _registry_connection(str(registry) if registry else None) as conn:
            projects = list_projects(conn)

            if not projects:
                console.print("プロジェクトがありません")
                return

            # Create table
            table = Table(title="プロジェクト一覧")
            table.add_column("ID", style="cyan")
            table.add_column("名前", style="green")
            table.add_column("ステータス", style="yellow")
            table.add_column("LLM", style="magenta")
            table.add_column("ドキュメント", style="blue")

            for proj in projects:
                llm_info = f"{proj.llm_provider}"
                if proj.llm_model:
                    llm_info += f" ({proj.llm_model})"

                status_color = {
                    ProjectStatus.CREATED: "white",
                    ProjectStatus.RUNNING: "yellow",
                    ProjectStatus.COMPLETED: "green",
                    ProjectStatus.ERROR: "red",
                }.get(proj.status, "white")

                table.add_row(
                    str(proj.id),
                    proj.name,
                    f"[{status_color}]{proj.status.value}[/{status_color}]",
                    llm_info,
                    proj.doc_root,
                )

            console.print(table)

    except Exception as e:
        console.print(f"[red]エラー: {e}[/red]")
        raise click.Abort()


@project.command()
@click.argument("name")
@click.option(
    "--registry",
    type=click.Path(path_type=Path),
    help="レジストリDBのパス (デフォルト: ~/.genglossary/registry.db)",
)
def delete(name: str, registry: Path | None):
    """プロジェクトを削除する

    注意: プロジェクトのDBファイルは削除されません。
    """
    try:
        with _registry_connection(str(registry) if registry else None) as conn:
            # Find project by name
            proj = get_project_by_name(conn, name)
            if proj is None:
                console.print(f"[yellow]プロジェクトが見つかりません: {name}[/yellow]")
                return

            # Delete project
            assert proj.id is not None, "Project ID must exist for deletion"
            with transaction(conn):
                delete_project(conn, proj.id)

            console.print(f"[green]✓[/green] プロジェクトを削除しました: {name}")

    except Exception as e:
        console.print(f"[red]エラー: {e}[/red]")
        raise click.Abort()


@project.command()
@click.argument("source_name")
@click.argument("new_name")
@click.option(
    "--registry",
    type=click.Path(path_type=Path),
    help="レジストリDBのパス (デフォルト: ~/.genglossary/registry.db)",
)
def clone(source_name: str, new_name: str, registry: Path | None):
    """プロジェクトを複製する"""
    try:
        with _registry_connection(str(registry) if registry else None) as conn:
            # Find source project
            source = get_project_by_name(conn, source_name)
            if source is None:
                console.print(f"[red]プロジェクトが見つかりません: {source_name}[/red]")
                raise click.Abort()

            # Get new project DB path
            new_db_path = _get_project_db_path(registry, new_name)

            # Clone project
            assert source.id is not None, "Source project must have an ID"
            with transaction(conn):
                new_id = clone_project(
                    conn,
                    source.id,
                    new_name=new_name,
                    new_db_path=str(new_db_path),
                )

            console.print(
                f"[green]✓[/green] プロジェクトを複製しました: {source_name} → {new_name}"
            )
            console.print(f"  新しいID: {new_id}")

    except Exception as e:
        console.print(f"[red]エラー: {e}[/red]")
        raise click.Abort()
