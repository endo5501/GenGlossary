"""Project CLI commands for GenGlossary."""

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

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


def _get_registry_conn(registry_path: str | None):
    """Get registry database connection.

    Args:
        registry_path: Optional path to registry database.
                      If None, uses default path.

    Returns:
        SQLite connection to registry database.
    """
    if registry_path is None:
        registry_path = str(get_default_registry_path())

    conn = get_registry_connection(registry_path)
    initialize_registry(conn)
    return conn


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
        conn = _get_registry_conn(str(registry) if registry else None)

        # Determine project DB path
        if registry:
            registry_dir = registry.parent / "projects"
        else:
            registry_dir = get_default_registry_path().parent / "projects"

        registry_dir.mkdir(parents=True, exist_ok=True)
        project_db_path = registry_dir / name / "project.db"
        project_db_path.parent.mkdir(parents=True, exist_ok=True)

        # Create project
        project_id = create_project(
            conn,
            name=name,
            doc_root=str(doc_root.absolute()),
            db_path=str(project_db_path),
            llm_provider=llm_provider,
            llm_model=llm_model,
        )

        conn.close()

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
        conn = _get_registry_conn(str(registry) if registry else None)
        projects = list_projects(conn)
        conn.close()

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
        conn = _get_registry_conn(str(registry) if registry else None)

        # Find project by name
        proj = get_project_by_name(conn, name)
        if proj is None:
            console.print(f"[yellow]プロジェクトが見つかりません: {name}[/yellow]")
            conn.close()
            return

        # Delete project
        delete_project(conn, proj.id)  # type: ignore
        conn.close()

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
        conn = _get_registry_conn(str(registry) if registry else None)

        # Find source project
        source = get_project_by_name(conn, source_name)
        if source is None:
            console.print(f"[red]プロジェクトが見つかりません: {source_name}[/red]")
            conn.close()
            raise click.Abort()

        # Determine new project DB path
        if registry:
            registry_dir = registry.parent / "projects"
        else:
            registry_dir = get_default_registry_path().parent / "projects"

        new_db_path = registry_dir / new_name / "project.db"
        new_db_path.parent.mkdir(parents=True, exist_ok=True)

        # Clone project
        new_id = clone_project(
            conn,
            source.id,  # type: ignore
            new_name=new_name,
            new_db_path=str(new_db_path),
        )

        conn.close()

        console.print(f"[green]✓[/green] プロジェクトを複製しました: {source_name} → {new_name}")
        console.print(f"  新しいID: {new_id}")

    except Exception as e:
        console.print(f"[red]エラー: {e}[/red]")
        raise click.Abort()
