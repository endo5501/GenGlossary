# データベース層 (Schema v4)

**役割**: SQLiteへのデータ永続化とCRUD操作

**Schema v4の主な変更点**:
- `documents`テーブルの`file_path`を`file_name`にリネーム
- `documents`テーブルに`content`カラムを追加（ファイル内容をDBに直接保存）
- `utils/hash.py`にハッシュ計算ユーティリティを追加

**Schema v3の主な変更点**:
- `runs`テーブルを再導入（バックグラウンド実行管理用）
- Run履歴の追跡とステータス管理をサポート
- `runs_repository.py`を追加

**過去のバージョン変更点**:
- `runs`テーブルを廃止し、`metadata`テーブル（単一行）に変更（v1→v2）
- 全てのrepository関数から`run_id`パラメータを削除（v1→v2）
- `glossary_helpers.py`で用語集関連の共通処理を集約（v1→v2）
- `runs`テーブルを再導入（v2→v3、ただし設計が異なる）

## connection.py
```python
import sqlite3
import uuid
from contextlib import contextmanager
from typing import Iterator

def get_connection(db_path: str) -> sqlite3.Connection:
    """データベース接続を取得"""
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.execute("PRAGMA busy_timeout = 5000")  # 一時的なロック対策 (5秒待機)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn

@contextmanager
def database_connection(db_path: str):
    """データベース接続のコンテキストマネージャー"""
    conn = get_connection(db_path)
    try:
        yield conn
    finally:
        conn.close()

@contextmanager
def transaction(conn: sqlite3.Connection) -> Iterator[None]:
    """トランザクション管理のコンテキストマネージャー

    ネストされたトランザクションをSQLite SAVEPOINTでサポート:
    - トップレベル: COMMIT/ROLLBACK
    - ネスト: SAVEPOINT/RELEASE/ROLLBACK TO

    正常終了時にcommit（またはRELEASE）、例外発生時にrollback。

    Usage:
        with database_connection(db_path) as conn:
            with transaction(conn):
                create_term(conn, "term1", ...)
                with transaction(conn):  # ネスト - SAVEPOINTを使用
                    create_term(conn, "term2", ...)
                # 両方の操作が成功した場合のみcommit
    """
    if conn.in_transaction:
        # ネストされたトランザクション - SAVEPOINTを使用
        savepoint_name = f"sp_{uuid.uuid4().hex[:8]}"
        conn.execute(f"SAVEPOINT {savepoint_name}")

        def release_savepoint() -> None:
            conn.execute(f"RELEASE {savepoint_name}")

        def rollback_savepoint() -> None:
            conn.execute(f"ROLLBACK TO {savepoint_name}")
            conn.execute(f"RELEASE {savepoint_name}")

        commit_fn = release_savepoint
        rollback_fn = rollback_savepoint
    else:
        # トップレベルトランザクション
        commit_fn = conn.commit
        rollback_fn = conn.rollback

    try:
        yield
        commit_fn()
    except Exception:
        rollback_fn()
        raise
```

## db_helpers.py
```python
from collections.abc import Sequence

def batch_insert(
    conn: sqlite3.Connection,
    table_name: str,
    columns: list[str],
    data: Sequence[tuple],
) -> None:
    """複数行を一括挿入する共通ヘルパー関数

    内部ヘルパー関数として使用。呼び出し側は以下を保証する必要があります:
    - table_name と columns は信頼できるリテラル値（ユーザー入力不可）
    - アトミック性が必要な場合は呼び出し側でトランザクション管理

    Args:
        table_name: 挿入先テーブル名（信頼できる値）
        columns: 挿入するカラム名のリスト（信頼できる値）
        data: 挿入する値のタプルのシーケンス

    Raises:
        sqlite3.IntegrityError: 制約違反時
        sqlite3.ProgrammingError: タプル長とカラム数不一致時
    """
    ...
```

## schema.py
```python
SCHEMA_VERSION = 4

def initialize_db(conn: sqlite3.Connection) -> None:
    """データベーススキーマを初期化 (Schema v4)"""
    # テーブル作成: metadata, documents, terms_extracted,
    # glossary_provisional, glossary_issues, glossary_refined, runs
    # metadataテーブルは単一行（id=1固定）でLLM設定や入力パスを保存
    # runsテーブルはバックグラウンド実行の履歴を管理
    #
    # documentsテーブル (v4):
    #   file_name TEXT NOT NULL UNIQUE  -- ファイル名または相対パス
    #     - GUI: ファイル名のみ (例: "chapter1.md")
    #     - CLI: doc_rootからの相対パス (例: "docs/chapter1.md")
    #   content TEXT NOT NULL           -- ファイル内容
    #   content_hash TEXT NOT NULL      -- SHA256ハッシュ
    ...

def get_schema_version(conn: sqlite3.Connection) -> int:
    """現在のスキーマバージョンを取得"""
    ...
```

## models.py
```python
from typing import TypedDict
from genglossary.models.term import TermOccurrence

class GlossaryTermRow(TypedDict):
    """用語集テーブル共通型 (provisional/refined) - Schema v2"""
    id: int
    term_name: str
    definition: str
    confidence: float
    occurrences: list[TermOccurrence]  # JSON文字列から復元

def serialize_occurrences(occurrences: list[TermOccurrence]) -> str:
    """TermOccurrenceをJSON文字列に変換"""
    ...

def deserialize_occurrences(json_str: str) -> list[TermOccurrence]:
    """JSON文字列をTermOccurrenceに変換"""
    ...
```

## metadata_repository.py
```python
def get_metadata(conn: sqlite3.Connection) -> sqlite3.Row | None:
    """メタデータを取得（単一行、id=1固定）"""
    ...

def upsert_metadata(
    conn: sqlite3.Connection,
    input_path: str,
    llm_provider: str,
    llm_model: str
) -> None:
    """メタデータを保存（UPSERT: id=1固定）

    SQLiteのON CONFLICT句を使用してUPSERTを実現。
    created_atは初回INSERT時にのみ設定され、更新時は保持される。
    """
    ...

def clear_metadata(conn: sqlite3.Connection) -> None:
    """メタデータを削除"""
    ...
```

## document_repository.py
```python
def create_document(
    conn: sqlite3.Connection,
    file_name: str,
    content: str,
    content_hash: str
) -> int:
    """ドキュメントを作成（file_name + content + hash）

    Returns:
        作成されたドキュメントのID

    Raises:
        sqlite3.IntegrityError: file_nameが既に存在する場合
    """
    ...

def get_document(conn: sqlite3.Connection, document_id: int) -> sqlite3.Row | None:
    """IDでドキュメントを取得"""
    ...

def get_document_by_name(conn: sqlite3.Connection, file_name: str) -> sqlite3.Row | None:
    """ファイル名でドキュメントを取得"""
    ...

def list_all_documents(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """全ドキュメントを取得（id順）"""
    ...

def delete_document(conn: sqlite3.Connection, document_id: int) -> None:
    """ドキュメントを削除"""
    ...

def delete_all_documents(conn: sqlite3.Connection) -> None:
    """全ドキュメントを削除"""
    ...

def create_documents_batch(
    conn: sqlite3.Connection,
    documents: Sequence[tuple[str, str, str]]
) -> None:
    """複数のドキュメントを一括作成（batch_insertヘルパー使用）

    Args:
        documents: (file_name, content, content_hash) のタプルのシーケンス

    Raises:
        sqlite3.IntegrityError: file_nameが既に存在する場合
    """
    batch_insert(conn, "documents", ["file_name", "content", "content_hash"], documents)
```

## term_repository.py
```python
def create_term(
    conn: sqlite3.Connection,
    term_text: str,
    category: str | None = None
) -> int:
    """抽出用語を作成（run_id不要）"""
    ...

def list_all_terms(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """全ての抽出用語を取得（run_id削除により、run_idフィルタ不要）"""
    ...

def get_term(conn: sqlite3.Connection, term_id: int) -> sqlite3.Row | None:
    """指定IDの用語を取得"""
    ...

def update_term(
    conn: sqlite3.Connection,
    term_id: int,
    term_text: str,
    category: str | None = None
) -> None:
    """用語を更新

    Raises:
        ValueError: 指定されたIDの用語が存在しない場合
    """
    ...

def delete_term(conn: sqlite3.Connection, term_id: int) -> None:
    """用語を削除"""
    ...

def delete_all_terms(conn: sqlite3.Connection) -> None:
    """全ての用語を削除"""
    ...

def create_terms_batch(
    conn: sqlite3.Connection,
    terms: Sequence[tuple[str, str | None]]
) -> None:
    """複数の用語を一括作成（パフォーマンス最適化）

    Args:
        terms: (term_text, category) のタプルのシーケンス

    Raises:
        sqlite3.IntegrityError: term_textが既に存在する場合
    """
    ...
```

## glossary_helpers.py
```python
from typing import Literal
from genglossary.models.term import TermOccurrence

# Type for glossary table names
GlossaryTable = Literal["glossary_provisional", "glossary_refined"]

# Allowed table names for SQL injection prevention
ALLOWED_TABLES: set[str] = {"glossary_provisional", "glossary_refined"}

def _validate_table_name(table_name: str) -> None:
    """テーブル名を検証（SQLインジェクション対策）

    Args:
        table_name: 検証するテーブル名

    Raises:
        ValueError: 許可されていないテーブル名の場合
    """
    if table_name not in ALLOWED_TABLES:
        raise ValueError(f"Invalid table name: {table_name}")

def create_glossary_term(
    conn: sqlite3.Connection,
    table_name: GlossaryTable,
    term_name: str,
    definition: str,
    confidence: float,
    occurrences: list[TermOccurrence]
) -> int:
    """用語集エントリを作成（provisional/refined共通）

    Args:
        table_name: "glossary_provisional" または "glossary_refined"
        term_name: 用語名
        definition: 定義
        confidence: 信頼度スコア (0.0 to 1.0)
        occurrences: 用語出現箇所のリスト

    Returns:
        作成されたエントリのID

    Raises:
        ValueError: table_nameが許可されていない場合
        sqlite3.IntegrityError: term_nameが既に存在する場合
    """
    ...

def get_glossary_term(
    conn: sqlite3.Connection,
    table_name: GlossaryTable,
    term_id: int
) -> GlossaryTermRow | None:
    """用語集エントリを取得（provisional/refined共通）

    Returns:
        GlossaryTermRow | None: デシリアライズされたoccurrencesを含むレコード、
            見つからない場合はNone
    """
    ...

def list_all_glossary_terms(
    conn: sqlite3.Connection,
    table_name: GlossaryTable
) -> list[GlossaryTermRow]:
    """全ての用語集エントリを取得（provisional/refined共通）

    Returns:
        デシリアライズされたoccurrencesを含むレコードのリスト
    """
    ...

def update_glossary_term(
    conn: sqlite3.Connection,
    table_name: GlossaryTable,
    term_id: int,
    definition: str,
    confidence: float
) -> None:
    """用語集エントリを更新（provisional/refined共通）

    Raises:
        ValueError: table_nameが許可されていない場合、または指定されたIDのエントリが存在しない場合
    """
    ...

def delete_all_glossary_terms(
    conn: sqlite3.Connection,
    table_name: GlossaryTable
) -> None:
    """全ての用語集エントリを削除（provisional/refined共通）

    Raises:
        ValueError: table_nameが許可されていない場合
    """
    ...

def create_glossary_terms_batch(
    conn: sqlite3.Connection,
    table_name: GlossaryTable,
    terms: list[tuple[str, str, float, list[TermOccurrence]]]
) -> None:
    """複数の用語集エントリを一括作成（パフォーマンス最適化）

    Args:
        table_name: "glossary_provisional" または "glossary_refined"
        terms: (term_name, definition, confidence, occurrences) のタプルのリスト

    Raises:
        ValueError: table_nameが許可されていない場合
        sqlite3.IntegrityError: term_nameが既に存在する場合
    """
    ...
```

## provisional_repository.py / refined_repository.py
```python
# provisional_repository.pyの例（refined_repository.pyも同様）
from genglossary.db.glossary_helpers import (
    create_glossary_term,
    get_glossary_term,
    list_all_glossary_terms,
    update_glossary_term,
    delete_all_glossary_terms,
)
from genglossary.db.models import GlossaryTermRow
from genglossary.models.term import TermOccurrence

def create_provisional_term(
    conn: sqlite3.Connection,
    term_name: str,
    definition: str,
    confidence: float,
    occurrences: list[TermOccurrence]
) -> int:
    """暫定用語集エントリを作成（run_id不要）

    Raises:
        sqlite3.IntegrityError: term_nameが既に存在する場合
    """
    return create_glossary_term(
        conn, "glossary_provisional", term_name, definition, confidence, occurrences
    )

def get_provisional_term(
    conn: sqlite3.Connection, term_id: int
) -> GlossaryTermRow | None:
    """指定IDの暫定用語を取得

    Returns:
        GlossaryTermRow | None: デシリアライズされたoccurrencesを含むレコード、
            見つからない場合はNone
    """
    return get_glossary_term(conn, "glossary_provisional", term_id)

def list_all_provisional(conn: sqlite3.Connection) -> list[GlossaryTermRow]:
    """全ての暫定用語集エントリを取得

    Returns:
        デシリアライズされたoccurrencesを含むレコードのリスト
    """
    return list_all_glossary_terms(conn, "glossary_provisional")

def update_provisional_term(
    conn: sqlite3.Connection,
    term_id: int,
    definition: str,
    confidence: float
) -> None:
    """暫定用語を更新

    Raises:
        ValueError: 指定されたIDのエントリが存在しない場合
    """
    update_glossary_term(conn, "glossary_provisional", term_id, definition, confidence)

def delete_all_provisional(conn: sqlite3.Connection) -> None:
    """全ての暫定用語集エントリを削除"""
    delete_all_glossary_terms(conn, "glossary_provisional")

def create_provisional_terms_batch(
    conn: sqlite3.Connection,
    terms: list[tuple[str, str, float, list[TermOccurrence]]]
) -> None:
    """複数の暫定用語集エントリを一括作成（パフォーマンス最適化）

    Args:
        terms: (term_name, definition, confidence, occurrences) のタプルのリスト

    Raises:
        sqlite3.IntegrityError: term_nameが既に存在する場合
    """
    create_glossary_terms_batch(conn, "glossary_provisional", terms)

# refined_repository.py にも同様の create_refined_terms_batch 関数あり
```

## プロジェクト管理システム

GUIアプリケーションで複数の用語集プロジェクトを管理するための機能を提供します。

### registry_connection.py
```python
from pathlib import Path

def get_default_registry_path() -> Path:
    """デフォルトのレジストリDBパスを取得

    Returns:
        ~/.genglossary/registry.db
    """
    return Path.home() / ".genglossary" / "registry.db"

def get_registry_connection(db_path: str) -> sqlite3.Connection:
    """レジストリデータベース接続を取得"""
    ...
```

### registry_schema.py
```python
REGISTRY_SCHEMA_VERSION = 2

def initialize_registry(conn: sqlite3.Connection) -> None:
    """レジストリDBスキーマを初期化

    Creates:
        - schema_version テーブル
        - projects テーブル（name, doc_root, db_path, llm_*, created_at, status）

    Migration v1→v2:
        - llm_base_url カラムを projects テーブルに追加
    """
    ...

def migrate_v1_to_v2(conn: sqlite3.Connection) -> None:
    """Add llm_base_url column to projects table."""
    conn.execute(
        "ALTER TABLE projects ADD COLUMN llm_base_url TEXT NOT NULL DEFAULT ''"
    )

def get_registry_schema_version(conn: sqlite3.Connection) -> int:
    """レジストリスキーマバージョンを取得"""
    ...
```

### project_repository.py
```python
from genglossary.models.project import Project, ProjectStatus

def create_project(
    conn: sqlite3.Connection,
    name: str,
    doc_root: str,
    db_path: str,
    llm_provider: str = "ollama",
    llm_model: str = "",
    llm_base_url: str = "",
    status: ProjectStatus = ProjectStatus.CREATED
) -> int:
    """プロジェクトを作成

    プロジェクトのメタデータをレジストリDBに登録し、
    プロジェクト固有のDBを初期化します。

    Returns:
        作成されたプロジェクトのID

    Raises:
        sqlite3.IntegrityError: nameまたはdb_pathが重複している場合
    """
    ...

def get_project(conn: sqlite3.Connection, project_id: int) -> Project | None:
    """IDでプロジェクトを取得"""
    ...

def get_project_by_name(conn: sqlite3.Connection, name: str) -> Project | None:
    """名前でプロジェクトを取得"""
    ...

def list_projects(conn: sqlite3.Connection) -> list[Project]:
    """全プロジェクトをリスト（created_at降順）"""
    ...

def update_project(
    conn: sqlite3.Connection,
    project_id: int,
    name: str | None = None,
    llm_provider: str | None = None,
    llm_model: str | None = None,
    llm_base_url: str | None = None,
    status: ProjectStatus | None = None,
    last_run_at: datetime | None = None
) -> None:
    """プロジェクト情報を更新

    updated_atは自動的に更新されます。
    name更新時は重複チェックが行われます（APIレベルで409エラー）。

    Raises:
        ValueError: 指定されたIDのプロジェクトが存在しない場合
    """
    ...

def delete_project(conn: sqlite3.Connection, project_id: int) -> None:
    """プロジェクトを削除

    Note: プロジェクトDBファイルは削除されません。
    """
    ...

def clone_project(
    conn: sqlite3.Connection,
    source_id: int,
    new_name: str,
    new_db_path: str
) -> int:
    """プロジェクトを複製

    設定（doc_root, llm_*）を継承し、statusはCREATED、
    last_run_atはNoneにリセットされます。

    Returns:
        複製されたプロジェクトのID

    Raises:
        ValueError: source_idのプロジェクトが存在しない場合
        sqlite3.IntegrityError: new_nameまたはnew_db_pathが重複している場合
    """
    ...
```

## ストレージ構造

```
~/.genglossary/
├── registry.db           # 中央プロジェクトレジストリ
└── projects/             # プロジェクトDBのデフォルト保存場所
    ├── my-novel/
    │   └── project.db    # プロジェクト固有のDB
    └── tech-docs/
        └── project.db
```

## データベース設計の原則

### Repository パターン
- 各テーブルに対して専用のrepositoryモジュールを作成
- CRUD操作を関数として実装（クラス化せず、シンプルに）
- 接続管理はrepositoryの外で行う（呼び出し元の責任）

### トランザクション管理
- **Repository関数はcommit/rollbackを行わない**（呼び出し元の責任）
- 書き込み操作には`transaction()`コンテキストマネージャを使用
- 複数の操作を1つのトランザクションにまとめて原子性を保証
- **ネストされたトランザクションをサポート**（SQLite SAVEPOINTを使用）

```python
# 正しいパターン: 呼び出し元がトランザクションを管理
from genglossary.db.connection import transaction

with database_connection(db_path) as conn:
    with transaction(conn):
        create_term(conn, "term1", ...)
        create_term(conn, "term2", ...)
        # 両方成功 → commit、どちらか失敗 → rollback

# ネストされたトランザクション: 内側は部分ロールバック可能
with database_connection(db_path) as conn:
    with transaction(conn):  # トップレベル
        create_term(conn, "outer", ...)
        try:
            with transaction(conn):  # ネスト - SAVEPOINTを使用
                create_term(conn, "inner", ...)
                raise ValueError("inner failed")
        except ValueError:
            pass  # 内側のみロールバック、外側は継続可能
        create_term(conn, "after_inner", ...)
        # outer と after_inner がコミットされる

# アンチパターン: repository関数内でのcommit（廃止）
# def create_term(conn, ...):
#     conn.execute(...)
#     conn.commit()  # これはやらない
```

### 型安全性
- `sqlite3.Row`を使用してカラム名でアクセス
- TypedDictで型ヒントを提供（`GlossaryTermRow`など）
- JSONシリアライズは専用関数で統一（`serialize_occurrences`など）
