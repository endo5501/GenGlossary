"""Database CLI commands for GenGlossary."""

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from genglossary.db.connection import get_connection
from genglossary.db.run_repository import get_latest_run, get_run, list_runs
from genglossary.db.schema import initialize_db
from genglossary.db.term_repository import (
    create_term,
    delete_term,
    get_term,
    list_terms_by_run,
    update_term,
)

console = Console()


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


@db.group()
def runs() -> None:
    """実行履歴の管理コマンド."""
    pass


@runs.command("list")
@click.option(
    "--db-path",
    type=click.Path(exists=True),
    default="./genglossary.db",
    help="Path to database file",
)
@click.option(
    "--limit",
    type=int,
    default=20,
    help="Maximum number of runs to display",
)
def runs_list(db_path: str, limit: int) -> None:
    """実行履歴の一覧を表示.

    Example:
        genglossary db runs list
        genglossary db runs list --limit 10
    """
    try:
        conn = get_connection(db_path)
        run_list = list_runs(conn, limit=limit)
        conn.close()

        if not run_list:
            console.print("[yellow]実行履歴がありません[/yellow]")
            return

        # Create table
        table = Table(title="実行履歴")
        table.add_column("ID", style="cyan")
        table.add_column("入力パス", style="magenta")
        table.add_column("プロバイダー", style="green")
        table.add_column("モデル", style="blue")
        table.add_column("ステータス", style="yellow")
        table.add_column("開始時刻", style="dim")

        for run in run_list:
            status_color = {
                "running": "yellow",
                "completed": "green",
                "failed": "red",
            }.get(run["status"], "white")

            table.add_row(
                str(run["id"]),
                run["input_path"],
                run["llm_provider"],
                run["llm_model"],
                f"[{status_color}]{run['status']}[/{status_color}]",
                run["started_at"],
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]エラー: {e}[/red]")
        raise click.Abort()


@runs.command("show")
@click.argument("run_id", type=int)
@click.option(
    "--db-path",
    type=click.Path(exists=True),
    default="./genglossary.db",
    help="Path to database file",
)
def runs_show(run_id: int, db_path: str) -> None:
    """指定されたrun_idの詳細を表示.

    Example:
        genglossary db runs show 1
    """
    try:
        conn = get_connection(db_path)
        run = get_run(conn, run_id)
        conn.close()

        if run is None:
            console.print(f"[red]Run ID {run_id} が見つかりません[/red]")
            raise click.Abort()

        # Display run details
        console.print(f"\n[bold]Run #{run['id']}[/bold]")
        console.print(f"入力パス: {run['input_path']}")
        console.print(f"プロバイダー: {run['llm_provider']}")
        console.print(f"モデル: {run['llm_model']}")
        console.print(f"ステータス: {run['status']}")
        console.print(f"開始時刻: {run['started_at']}")

        if run["completed_at"]:
            console.print(f"完了時刻: {run['completed_at']}")

        if run["error_message"]:
            console.print(f"[red]エラー: {run['error_message']}[/red]")

    except Exception as e:
        console.print(f"[red]エラー: {e}[/red]")
        raise click.Abort()


@runs.command("latest")
@click.option(
    "--db-path",
    type=click.Path(exists=True),
    default="./genglossary.db",
    help="Path to database file",
)
def runs_latest(db_path: str) -> None:
    """最新の実行履歴を表示.

    Example:
        genglossary db runs latest
    """
    try:
        conn = get_connection(db_path)
        run = get_latest_run(conn)
        conn.close()

        if run is None:
            console.print("[yellow]実行履歴がありません[/yellow]")
            return

        # Display run details (same as show command)
        console.print(f"\n[bold]Run #{run['id']} (最新)[/bold]")
        console.print(f"入力パス: {run['input_path']}")
        console.print(f"プロバイダー: {run['llm_provider']}")
        console.print(f"モデル: {run['llm_model']}")
        console.print(f"ステータス: {run['status']}")
        console.print(f"開始時刻: {run['started_at']}")

        if run["completed_at"]:
            console.print(f"完了時刻: {run['completed_at']}")

        if run["error_message"]:
            console.print(f"[red]エラー: {run['error_message']}[/red]")

    except Exception as e:
        console.print(f"[red]エラー: {e}[/red]")
        raise click.Abort()

@db.group()
def terms() -> None:
    """抽出用語の管理コマンド."""
    pass


@terms.command("list")
@click.option(
    "--run-id",
    type=int,
    required=True,
    help="Run ID to filter by",
)
@click.option(
    "--db-path",
    type=click.Path(exists=True),
    default="./genglossary.db",
    help="Path to database file",
)
def terms_list(run_id: int, db_path: str) -> None:
    """指定されたrun_idの抽出用語一覧を表示.

    Example:
        genglossary db terms list --run-id 1
    """
    try:
        conn = get_connection(db_path)
        term_list = list_terms_by_run(conn, run_id)
        conn.close()

        if not term_list:
            console.print("[yellow]用語がありません[/yellow]")
            return

        # Create table
        table = Table(title=f"抽出用語 (Run #{run_id})")
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
        console.print(f"Run ID: {term['run_id']}")

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
    "--run-id",
    type=int,
    required=True,
    help="Run ID to associate terms with",
)
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
def terms_import(run_id: int, file: str, db_path: str) -> None:
    """テキストファイルから用語をインポート（1行1用語）.

    Example:
        genglossary db terms import --run-id 1 --file terms.txt
    """
    try:
        # Read terms from file
        with open(file, "r", encoding="utf-8") as f:
            term_texts = [line.strip() for line in f if line.strip()]

        # Import terms
        conn = get_connection(db_path)
        for term_text in term_texts:
            create_term(conn, run_id, term_text)
        conn.close()

        console.print(
            f"[green]✓[/green] {len(term_texts)}件の用語をインポートしました"
        )

    except Exception as e:
        console.print(f"[red]エラー: {e}[/red]")
        raise click.Abort()
