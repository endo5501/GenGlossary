# アーキテクチャガイド

このドキュメントでは、GenGlossaryプロジェクトの全体構造、ディレクトリ構成、モジュール設計について説明します。

## ディレクトリ構成

```
GenGlossary/
├── src/genglossary/              # メインパッケージ
│   ├── __init__.py
│   ├── models/                   # データモデル
│   │   ├── __init__.py
│   │   ├── document.py          # Document, Line管理
│   │   ├── term.py              # Term, TermOccurrence
│   │   ├── glossary.py          # Glossary, GlossaryIssue
│   │   └── project.py           # Project, ProjectStatus
│   ├── llm/                      # LLMクライアント
│   │   ├── __init__.py
│   │   ├── base.py              # BaseLLMClient
│   │   ├── ollama_client.py     # OllamaClient
│   │   ├── openai_compatible_client.py  # OpenAICompatibleClient
│   │   └── factory.py           # LLMクライアントファクトリ
│   ├── db/                       # データベース層 (Schema v2)
│   │   ├── __init__.py
│   │   ├── connection.py        # SQLite接続管理
│   │   ├── schema.py            # スキーマ定義・初期化
│   │   ├── models.py            # DB用TypedDict・シリアライズ
│   │   ├── metadata_repository.py    # メタデータCRUD
│   │   ├── document_repository.py    # ドキュメントCRUD
│   │   ├── term_repository.py   # 抽出用語CRUD
│   │   ├── glossary_helpers.py  # 用語集共通処理
│   │   ├── provisional_repository.py # 暫定用語集CRUD
│   │   ├── issue_repository.py  # 精査結果CRUD
│   │   ├── refined_repository.py     # 最終用語集CRUD
│   │   ├── registry_connection.py    # レジストリDB接続管理
│   │   ├── registry_schema.py   # レジストリスキーマ定義
│   │   └── project_repository.py     # プロジェクトCRUD
│   ├── document_loader.py        # ドキュメント読み込み
│   ├── term_extractor.py         # ステップ1: 用語抽出
│   ├── glossary_generator.py     # ステップ2: 用語集生成
│   ├── glossary_reviewer.py      # ステップ3: 精査
│   ├── glossary_refiner.py       # ステップ4: 改善
│   ├── output/
│   │   ├── __init__.py
│   │   └── markdown_writer.py    # Markdown出力
│   ├── api/                       # FastAPI バックエンド
│   │   ├── __init__.py
│   │   ├── app.py                # アプリファクトリ
│   │   ├── dependencies.py       # DI (設定、DB接続、プロジェクト取得)
│   │   ├── schemas/              # APIスキーマ
│   │   │   ├── __init__.py
│   │   │   ├── common.py         # 共通スキーマ (Health, Version, GlossaryTermResponse)
│   │   │   ├── term_schemas.py   # Terms用スキーマ
│   │   │   ├── provisional_schemas.py  # Provisional用スキーマ
│   │   │   ├── issue_schemas.py  # Issues用スキーマ
│   │   │   ├── refined_schemas.py      # Refined用スキーマ
│   │   │   └── file_schemas.py   # Files用スキーマ
│   │   ├── middleware/
│   │   │   ├── __init__.py
│   │   │   ├── request_id.py    # リクエストIDミドルウェア
│   │   │   └── logging.py       # 構造化ログミドルウェア
│   │   └── routers/
│   │       ├── __init__.py
│   │       ├── health.py        # /health, /version
│   │       ├── terms.py         # /api/projects/{project_id}/terms
│   │       ├── provisional.py   # /api/projects/{project_id}/provisional
│   │       ├── issues.py        # /api/projects/{project_id}/issues
│   │       ├── refined.py       # /api/projects/{project_id}/refined
│   │       └── files.py         # /api/projects/{project_id}/files
│   ├── config.py                 # 設定管理
│   ├── cli.py                    # CLIエントリーポイント (generate)
│   ├── cli_db.py                 # DB管理CLI (db サブコマンド)
│   ├── cli_project.py            # プロジェクト管理CLI (project サブコマンド)
│   └── cli_api.py                # API管理CLI (api サブコマンド)
├── tests/                        # テストコード
│   ├── api/                       # API層テスト
│   │   ├── __init__.py
│   │   ├── conftest.py          # APIテスト用fixture
│   │   ├── test_app.py          # FastAPIアプリテスト
│   │   ├── test_dependencies.py # 依存性注入テスト
│   │   └── routers/             # Routerテスト
│   │       ├── test_terms.py    # Terms APIテスト (8 tests)
│   │       ├── test_provisional.py  # Provisional APIテスト (9 tests)
│   │       ├── test_issues.py   # Issues APIテスト (6 tests)
│   │       ├── test_refined.py  # Refined APIテスト (7 tests)
│   │       └── test_files.py    # Files APIテスト (11 tests)
│   ├── models/
│   │   ├── test_document.py
│   │   ├── test_term.py
│   │   ├── test_glossary.py
│   │   └── test_project.py
│   ├── llm/
│   │   ├── test_base.py
│   │   └── test_ollama_client.py
│   ├── db/                       # DB層テスト
│   │   ├── conftest.py          # DBテスト用fixture
│   │   ├── test_connection.py
│   │   ├── test_schema.py
│   │   ├── test_models.py
│   │   ├── test_metadata_repository.py
│   │   ├── test_document_repository.py
│   │   ├── test_term_repository.py
│   │   ├── test_provisional_repository.py
│   │   ├── test_issue_repository.py
│   │   ├── test_refined_repository.py
│   │   ├── test_registry_schema.py
│   │   └── test_project_repository.py
│   ├── test_document_loader.py
│   ├── test_term_extractor.py
│   ├── test_glossary_generator.py
│   ├── test_glossary_reviewer.py
│   ├── test_glossary_refiner.py
│   ├── test_cli_db.py           # DB CLI統合テスト
│   ├── test_cli_db_regenerate.py # regenerateコマンドテスト
│   ├── test_cli_project.py      # プロジェクトCLI統合テスト
│   └── output/
│       └── test_markdown_writer.py
├── target_docs/                  # 入力ドキュメント
├── output/                       # 生成された用語集
├── scripts/                      # ユーティリティスクリプト
│   └── ticket.sh                # チケット管理
├── .claude/                      # Claudeルール
│   ├── CLAUDE.md
│   └── rules/
├── pyproject.toml                # プロジェクト設定
└── uv.lock                       # 依存関係ロック
```

## モジュール構成

### 1. models/ - データモデル層

**役割**: ドメインモデルの定義

#### document.py
```python
from pydantic import BaseModel

class Document(BaseModel):
    """ドキュメントを表すモデル"""
    file_path: str
    content: str

    def get_line(self, line_number: int) -> str:
        """行番号から行を取得"""
        ...

    def get_context(self, line_number: int, context_lines: int = 1) -> list[str]:
        """行とその前後のコンテキストを取得"""
        ...
```

#### term.py
```python
from enum import Enum

class TermCategory(str, Enum):
    """用語のカテゴリ分類"""
    PERSON_NAME = "person_name"       # 人名
    PLACE_NAME = "place_name"         # 地名
    ORGANIZATION = "organization"     # 組織・団体名
    TITLE = "title"                   # 役職・称号
    TECHNICAL_TERM = "technical_term" # 専門用語
    COMMON_NOUN = "common_noun"       # 一般名詞（除外対象）

class ClassifiedTerm(BaseModel):
    """分類済みの用語（カテゴリ付き）"""
    term: str
    category: TermCategory

class Term(BaseModel):
    """用語を表すモデル"""
    name: str
    definition: str
    occurrences: list[TermOccurrence]
    confidence: float  # 0.0-1.0

class TermOccurrence(BaseModel):
    """用語の出現箇所"""
    document_path: str
    line_number: int
    context: str
```

#### glossary.py
```python
class Glossary(BaseModel):
    """用語集を表すモデル"""
    terms: list[Term]

class GlossaryIssue(BaseModel):
    """用語集の問題点"""
    term: str
    issue_type: str  # "unclear", "contradiction", "missing"
    description: str
```

#### project.py
```python
from enum import Enum
from datetime import datetime

class ProjectStatus(str, Enum):
    """プロジェクトのステータス"""
    CREATED = "created"       # 作成済み（未実行）
    RUNNING = "running"       # 処理中
    COMPLETED = "completed"   # 完了
    ERROR = "error"          # エラー

class Project(BaseModel):
    """用語集生成プロジェクト"""
    id: int | None
    name: str                 # プロジェクト名（一意）
    doc_root: str            # ドキュメントディレクトリパス
    db_path: str             # プロジェクトDBパス（一意）
    llm_provider: str        # LLMプロバイダー
    llm_model: str           # LLMモデル名
    created_at: datetime
    updated_at: datetime
    last_run_at: datetime | None
    status: ProjectStatus
```

### 2. llm/ - LLMクライアント層

**役割**: LLMとの通信を抽象化

#### base.py
```python
from abc import ABC, abstractmethod

class BaseLLMClient(ABC):
    """LLMクライアントの基底クラス"""

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """テキスト生成"""
        ...

    @abstractmethod
    def generate_structured(self, prompt: str, response_model: type[BaseModel]) -> BaseModel:
        """構造化出力生成"""
        ...
```

#### ollama_client.py
```python
import httpx
from pydantic import BaseModel

class OllamaClient(BaseLLMClient):
    """Ollama APIクライアント"""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.client = httpx.Client()

    def generate(self, prompt: str) -> str:
        """Ollama APIでテキスト生成"""
        ...
```

#### factory.py
```python
from genglossary.llm.base import BaseLLMClient
from genglossary.llm.ollama_client import OllamaClient
from genglossary.llm.openai_compatible_client import OpenAICompatibleClient

def create_llm_client(
    provider: str,
    model: str | None = None,
    openai_base_url: str | None = None,
    timeout: float = 180.0,
) -> BaseLLMClient:
    """LLMクライアントを生成するファクトリ関数

    cli.pyとcli_db.pyの循環インポートを解決するために導入。
    プロバイダに応じて適切なLLMクライアントインスタンスを返す。

    Args:
        provider: "ollama" または "openai"
        model: モデル名（省略時はデフォルト値）
        openai_base_url: OpenAI互換APIのベースURL
        timeout: タイムアウト秒数

    Returns:
        初期化されたLLMクライアント

    Raises:
        ValueError: 未知のプロバイダが指定された場合
    """
    ...
```

**循環インポート解決の経緯:**
- 以前は`create_llm_client`が`cli.py`に定義されていた
- `cli_db.py`が`create_llm_client`を使用するため`cli.py`をimport
- `cli.py`が`cli_db.py`の`db`コマンドグループをimport
- この相互依存により循環インポートエラーが発生
- `create_llm_client`を独立した`factory.py`に移動することで解決

### 3. db/ - データベース層 (Schema v2)

**役割**: SQLiteへのデータ永続化とCRUD操作

**Schema v2の主な変更点**:
- `runs`テーブルを廃止し、`metadata`テーブル（単一行）に変更
- 全てのrepository関数から`run_id`パラメータを削除
- `glossary_helpers.py`で用語集関連の共通処理を集約

#### connection.py
```python
import sqlite3
from contextlib import contextmanager

def get_connection(db_path: str) -> sqlite3.Connection:
    """データベース接続を取得"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

@contextmanager
def database_connection(db_path: str):
    """データベース接続のコンテキストマネージャー"""
    conn = get_connection(db_path)
    try:
        yield conn
    finally:
        conn.close()
```

#### schema.py
```python
def initialize_db(conn: sqlite3.Connection) -> None:
    """データベーススキーマを初期化 (Schema v2)"""
    # テーブル作成: metadata, documents, terms_extracted,
    # glossary_provisional, glossary_issues, glossary_refined
    # metadataテーブルは単一行（id=1固定）でLLM設定や入力パスを保存
    ...

def get_schema_version(conn: sqlite3.Connection) -> int:
    """現在のスキーマバージョンを取得"""
    ...
```

#### models.py
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

#### metadata_repository.py
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

#### term_repository.py
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
```

#### glossary_helpers.py
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
```

#### provisional_repository.py / refined_repository.py
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
```

#### プロジェクト管理システム

GUIアプリケーションで複数の用語集プロジェクトを管理するための機能を提供します。

##### registry_connection.py
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

##### registry_schema.py
```python
REGISTRY_SCHEMA_VERSION = 1

def initialize_registry(conn: sqlite3.Connection) -> None:
    """レジストリDBスキーマを初期化

    Creates:
        - schema_version テーブル
        - projects テーブル（name, doc_root, db_path, llm_*, created_at, status）
    """
    ...

def get_registry_schema_version(conn: sqlite3.Connection) -> int:
    """レジストリスキーマバージョンを取得"""
    ...
```

##### project_repository.py
```python
from genglossary.models.project import Project, ProjectStatus

def create_project(
    conn: sqlite3.Connection,
    name: str,
    doc_root: str,
    db_path: str,
    llm_provider: str = "ollama",
    llm_model: str = "",
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
    llm_provider: str | None = None,
    llm_model: str | None = None,
    status: ProjectStatus | None = None,
    last_run_at: datetime | None = None
) -> None:
    """プロジェクト情報を更新

    updated_atは自動的に更新されます。

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

**ストレージ構造**:
```
~/.genglossary/
├── registry.db           # 中央プロジェクトレジストリ
└── projects/             # プロジェクトDBのデフォルト保存場所
    ├── my-novel/
    │   └── project.db    # プロジェクト固有のDB
    └── tech-docs/
        └── project.db
```

### 4. 処理レイヤー

#### document_loader.py
```python
def load_document(file_path: str) -> Document:
    """ファイルからドキュメントを読み込む"""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    return Document(file_path=file_path, content=content)
```

#### term_extractor.py (ステップ1)
```python
from typing import overload

class TermExtractor:
    """用語抽出を行うクラス（SudachiPy形態素解析 + LLM分類）"""

    def __init__(self, llm_client: BaseLLMClient):
        self.llm_client = llm_client

    @overload
    def extract_terms(
        self,
        documents: list[Document],
        progress_callback: ProgressCallback | None = None,
        batch_size: int = 10,
        *,
        return_categories: bool = False,
    ) -> list[str]: ...

    @overload
    def extract_terms(
        self,
        documents: list[Document],
        progress_callback: ProgressCallback | None = None,
        batch_size: int = 10,
        *,
        return_categories: bool = True,
    ) -> list[ClassifiedTerm]: ...

    def extract_terms(
        self,
        documents: list[Document],
        progress_callback: ProgressCallback | None = None,
        batch_size: int = 10,
        *,
        return_categories: bool = False,
    ) -> list[str] | list[ClassifiedTerm]:
        """ドキュメントから用語を抽出

        Args:
            documents: 処理対象のドキュメントリスト
            progress_callback: 進捗コールバック（オプション）
            batch_size: LLM分類のバッチサイズ（デフォルト: 10）
            return_categories: Trueの場合、カテゴリ付きで返す

        Returns:
            return_categories=False: list[str] (common_noun除外)
            return_categories=True: list[ClassifiedTerm] (全カテゴリ含む)
        """
        ...
```

#### glossary_generator.py (ステップ2)
```python
class GlossaryGenerator:
    """用語集生成を行うクラス"""

    def __init__(self, llm_client: BaseLLMClient):
        self.llm_client = llm_client

    def generate(
        self,
        terms: list[str] | list[ClassifiedTerm],
        documents: list[Document],
        progress_callback: ProgressCallback | None = None,
        skip_common_nouns: bool = True,
    ) -> Glossary:
        """用語集を生成

        Args:
            terms: 用語リスト（str または ClassifiedTerm）
            documents: ドキュメントリスト
            progress_callback: 進捗コールバック（オプション）
            skip_common_nouns: ClassifiedTerm使用時にcommon_nounをスキップ

        Returns:
            生成された用語集
        """
        ...
```

#### glossary_reviewer.py (ステップ3)
```python
class GlossaryReviewer:
    """用語集の精査を行うクラス"""

    def __init__(self, llm_client: BaseLLMClient):
        self.llm_client = llm_client

    def review(self, glossary: Glossary) -> list[GlossaryIssue]:
        """用語集を精査し、問題点を列挙"""
        ...
```

#### glossary_refiner.py (ステップ4)
```python
class GlossaryRefiner:
    """用語集の改善を行うクラス"""

    def __init__(self, llm_client: BaseLLMClient):
        self.llm_client = llm_client

    def refine(self, glossary: Glossary, issues: list[GlossaryIssue], document: Document) -> Glossary:
        """問題点に基づいて用語集を改善"""
        ...
```

### 5. output/ - 出力層

#### markdown_writer.py
```python
def write_glossary(glossary: Glossary, output_path: str) -> None:
    """用語集をMarkdown形式で出力"""
    ...
```

### 6. api/ - API層（FastAPI バックエンド）

**役割**: GUIアプリケーションのためのREST APIを提供

#### app.py (アプリケーションファクトリ)
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

def create_app() -> FastAPI:
    """FastAPIアプリケーションを作成"""
    app = FastAPI(
        title="GenGlossary API",
        description="API for GenGlossary",
        version=__version__,
    )

    # CORS設定（localhost:3000, 5173など）
    app.add_middleware(CORSMiddleware, ...)

    # カスタムミドルウェア
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(StructuredLoggingMiddleware)

    # ルーター登録
    app.include_router(health_router)

    return app
```

#### schemas/ (APIスキーマ)

スキーマはエンティティごとにモジュール化されています。

##### common.py (共通スキーマ)
```python
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from genglossary.models.term import TermOccurrence


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Health status")
    timestamp: datetime = Field(..., description="Current timestamp")


class VersionResponse(BaseModel):
    """Version information response."""
    name: str = Field(..., description="Application name")
    version: str = Field(..., description="Application version")


class GlossaryTermResponse(BaseModel):
    """Common schema for glossary terms (provisional and refined)."""
    id: int = Field(..., description="Term ID")
    term_name: str = Field(..., description="Term name")
    definition: str = Field(..., description="Term definition")
    confidence: float = Field(..., description="Confidence score (0.0 to 1.0)")
    occurrences: list[TermOccurrence] = Field(
        ..., description="List of term occurrences"
    )

    @classmethod
    def from_db_row(cls, row: Any) -> "GlossaryTermResponse":
        """Create from database row.

        Args:
            row: Database row (GlossaryTermRow or dict-like) with deserialized occurrences.

        Returns:
            GlossaryTermResponse: Response instance.
        """
        return cls(
            id=row["id"],
            term_name=row["term_name"],
            definition=row["definition"],
            confidence=row["confidence"],
            occurrences=row["occurrences"],
        )

    @classmethod
    def from_db_rows(cls, rows: list[Any]) -> list["GlossaryTermResponse"]:
        """Create list from database rows.

        Args:
            rows: List of database rows (GlossaryTermRow or dict-like).

        Returns:
            list[GlossaryTermResponse]: List of response instances.
        """
        return [cls.from_db_row(row) for row in rows]
```

##### term_schemas.py (Terms用スキーマ)
```python
class TermResponse(BaseModel):
    """Response schema for a term."""
    id: int = Field(..., description="Term ID")
    term_text: str = Field(..., description="Term text")
    category: str | None = Field(None, description="Term category")

    @classmethod
    def from_db_row(cls, row: Any) -> "TermResponse":
        """Create from database row."""
        return cls(
            id=row["id"],
            term_text=row["term_text"],
            category=row["category"],
        )

    @classmethod
    def from_db_rows(cls, rows: list[Any]) -> list["TermResponse"]:
        """Create list from database rows."""
        return [cls.from_db_row(row) for row in rows]


class TermMutationRequest(BaseModel):
    """Request schema for creating or updating a term."""
    term_text: str = Field(..., description="Term text")
    category: str | None = Field(None, description="Term category")


# Aliases for clarity
TermCreateRequest = TermMutationRequest
TermUpdateRequest = TermMutationRequest
```

##### provisional_schemas.py / refined_schemas.py
```python
# GlossaryTermResponseを継承またはエイリアス
from genglossary.api.schemas.common import GlossaryTermResponse

ProvisionalResponse = GlossaryTermResponse  # Provisional用
RefinedResponse = GlossaryTermResponse      # Refined用
```

##### issue_schemas.py (Issues用スキーマ)
```python
class IssueResponse(BaseModel):
    """Response schema for a glossary issue."""
    id: int = Field(..., description="Issue ID")
    term_name: str = Field(..., description="Term name this issue relates to")
    issue_type: str = Field(..., description="Type of issue")
    description: str = Field(..., description="Description of the issue")

    @classmethod
    def from_db_row(cls, row: Any) -> "IssueResponse":
        """Create from database row."""
        return cls(
            id=row["id"],
            term_name=row["term_name"],
            issue_type=row["issue_type"],
            description=row["description"],
        )

    @classmethod
    def from_db_rows(cls, rows: list[Any]) -> list["IssueResponse"]:
        """Create list from database rows."""
        return [cls.from_db_row(row) for row in rows]
```

##### file_schemas.py (Files用スキーマ)
```python
class FileResponse(BaseModel):
    """Response schema for a document file."""
    id: int = Field(..., description="Document ID")
    file_path: str = Field(..., description="File path")
    content_hash: str = Field(..., description="Content hash")

    @classmethod
    def from_db_row(cls, row: Any) -> "FileResponse":
        """Create from database row."""
        return cls(
            id=row["id"],
            file_path=row["file_path"],
            content_hash=row["content_hash"],
        )

    @classmethod
    def from_db_rows(cls, rows: list[Any]) -> list["FileResponse"]:
        """Create list from database rows."""
        return [cls.from_db_row(row) for row in rows]


class FileCreateRequest(BaseModel):
    """Request schema for creating a document file."""
    file_path: str = Field(..., description="File path relative to doc_root")


class DiffScanResponse(BaseModel):
    """Response schema for diff scan operation."""
    added: list[str] = Field(..., description="List of newly added file paths")
    modified: list[str] = Field(..., description="List of modified file paths")
    deleted: list[str] = Field(..., description="List of deleted file paths")
```

**スキーマ設計のポイント:**
- `from_db_row()` / `from_db_rows()` クラスメソッドでDB行からモデルへの変換を統一
- `GlossaryTermResponse` を基底クラスとしてProvisionalとRefinedで共有
- `TermMutationRequest` をCreateとUpdateで共有（DRY原則）
- `Field()` でOpenAPIドキュメントに説明を追加

#### routers/ (APIエンドポイント)

##### health.py (ヘルスチェックエンドポイント)
```python
from fastapi import APIRouter

router = APIRouter(tags=["health"])

@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """ヘルスチェック"""
    return HealthResponse(status="ok", timestamp=datetime.now(timezone.utc))

@router.get("/version", response_model=VersionResponse)
async def version_info() -> VersionResponse:
    """バージョン情報"""
    return VersionResponse(name="genglossary", version=__version__)
```

##### terms.py (Terms API - 抽出用語の管理)
```python
from fastapi import APIRouter, Body, Depends, HTTPException, Path, status

router = APIRouter(prefix="/api/projects/{project_id}/terms", tags=["terms"])

@router.get("", response_model=list[TermResponse])
async def list_all_terms_endpoint(
    project_id: int = Path(...),
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> list[TermResponse]:
    """抽出用語の一覧を取得"""
    rows = list_all_terms(project_db)
    return TermResponse.from_db_rows(rows)

@router.get("/{term_id}", response_model=TermResponse)
async def get_term_endpoint(
    project_id: int = Path(...),
    term_id: int = Path(...),
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> TermResponse:
    """指定IDの用語を取得"""
    row = get_term(project_db, term_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Term not found")
    return TermResponse.from_db_row(row)

@router.post("", response_model=TermResponse, status_code=status.HTTP_201_CREATED)
async def create_new_term(
    project_id: int = Path(...),
    request: TermCreateRequest = Body(...),
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> TermResponse:
    """新しい用語を作成"""
    term_id = create_term(project_db, request.term_text, request.category)
    row = get_term(project_db, term_id)
    assert row is not None
    return TermResponse.from_db_row(row)

@router.patch("/{term_id}", response_model=TermResponse)
async def update_term_endpoint(
    project_id: int = Path(...),
    term_id: int = Path(...),
    request: TermUpdateRequest = Body(...),
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> TermResponse:
    """用語を更新"""
    update_term(project_db, term_id, request.term_text, request.category)
    row = get_term(project_db, term_id)
    assert row is not None
    return TermResponse.from_db_row(row)

@router.delete("/{term_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_term_endpoint(
    project_id: int = Path(...),
    term_id: int = Path(...),
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> None:
    """用語を削除"""
    delete_term(project_db, term_id)
```

##### provisional.py (Provisional API - 暫定用語集)
```python
router = APIRouter(prefix="/api/projects/{project_id}/provisional", tags=["provisional"])

# GET /api/projects/{project_id}/provisional - 一覧取得
# GET /api/projects/{project_id}/provisional/{entry_id} - 詳細取得
# PATCH /api/projects/{project_id}/provisional/{entry_id} - 更新
# DELETE /api/projects/{project_id}/provisional/{entry_id} - 削除
# POST /api/projects/{project_id}/provisional/{entry_id}/regenerate - 単一エントリの再生成（LLM）
```

**regenerate エンドポイントの実装詳細:**

```python
@router.post("/{entry_id}/regenerate", response_model=ProvisionalResponse)
async def regenerate_provisional(
    project_id: int = Path(..., description="Project ID"),
    entry_id: int = Path(..., description="Entry ID"),
    project: Project = Depends(get_project_by_id),
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> ProvisionalResponse:
    """Regenerate definition for a provisional term using LLM.

    処理フロー:
    1. 用語の存在確認（get_provisional_term）
    2. プロジェクトのLLM設定からLLMクライアント作成
    3. DocumentLoaderでドキュメントロード
    4. GlossaryGeneratorで用語の出現箇所検索と定義再生成
    5. 新しい定義とconfidenceでDB更新
    6. 更新後の用語を返却

    エラーハンドリング:
    - 404: 用語が見つからない場合
    - 503: LLMタイムアウト (httpx.TimeoutException)
    - 503: LLM接続エラー (httpx.HTTPError)

    Returns:
        ProvisionalResponse: 再生成された用語（新しい定義とconfidence）
    """
    # 用語の存在確認
    row = get_provisional_term(project_db, entry_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Entry {entry_id} not found")

    try:
        # LLMクライアント作成
        llm_client = create_llm_client(project.llm_provider, project.llm_model or None)

        # ドキュメントロード
        loader = DocumentLoader()
        documents = loader.load_directory(project.doc_root)

        # 定義再生成
        generator = GlossaryGenerator(llm_client=llm_client)
        occurrences = generator._find_term_occurrences(row["term_name"], documents)
        if not occurrences:
            occurrences = row["occurrences"]  # 既存のoccurrencesを使用

        definition, confidence = generator._generate_definition(
            row["term_name"], occurrences
        )

        # DB更新
        update_provisional_term(project_db, entry_id, definition, confidence)

        # 更新後の用語を返却
        updated_row = get_provisional_term(project_db, entry_id)
        return ProvisionalResponse.from_db_row(updated_row)

    except httpx.TimeoutException:
        raise HTTPException(status_code=503, detail="LLM service timeout")
    except httpx.HTTPError as e:
        raise HTTPException(status_code=503, detail=f"LLM service unavailable: {e}")
```

**LLM統合のポイント:**
- プロジェクトの `llm_provider` と `llm_model` 設定を使用
- `GlossaryGenerator._find_term_occurrences()` でドキュメント内の用語出現箇所を検索
- `GlossaryGenerator._generate_definition()` でLLMを使用して定義と信頼度を生成
- 既存のoccurrencesが見つからない場合は、DBに保存されているoccurrencesを使用

##### issues.py (Issues API - 精査結果)
```python
router = APIRouter(prefix="/api/projects/{project_id}/issues", tags=["issues"])

@router.get("", response_model=list[IssueResponse])
async def list_all_issues_endpoint(
    project_id: int = Path(...),
    issue_type: str | None = Query(None, description="Filter by issue type"),
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> list[IssueResponse]:
    """精査結果の一覧を取得（issue_typeフィルタ対応）"""
    if issue_type:
        rows = list_issues_by_type(project_db, issue_type)
    else:
        rows = list_all_issues(project_db)
    return IssueResponse.from_db_rows(rows)

# GET /api/projects/{project_id}/issues/{issue_id} - 詳細取得
```

##### refined.py (Refined API - 最終用語集)
```python
router = APIRouter(prefix="/api/projects/{project_id}/refined", tags=["refined"])

# GET /api/projects/{project_id}/refined - 一覧取得
# GET /api/projects/{project_id}/refined/{term_id} - 詳細取得
# GET /api/projects/{project_id}/refined/export-md - Markdownエクスポート
# PATCH /api/projects/{project_id}/refined/{term_id} - 更新
# DELETE /api/projects/{project_id}/refined/{term_id} - 削除

@router.get("/export-md", response_class=PlainTextResponse)
async def export_markdown(
    project_id: int = Path(...),
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> PlainTextResponse:
    """最終用語集をMarkdown形式でエクスポート"""
    rows = list_all_refined(project_db)
    lines = ["# 用語集\n"]
    for row in rows:
        lines.append(f"## {row['term_name']}\n")
        lines.append(f"{row['definition']}\n\n")
        # ... 出現箇所の追加
    return PlainTextResponse(
        content="".join(lines),
        media_type="text/markdown; charset=utf-8"
    )
```

**重要な実装ポイント:**
- `export-md` のような固定パスは `/{term_id}` より先に定義する（FastAPIのルーティング順序）
- `Body(...)` アノテーションでリクエストボディを明示
- プロジェクトIDの検証は `get_project_by_id` が自動的に404を返す

##### files.py (Files API - ドキュメント管理)
```python
router = APIRouter(prefix="/api/projects/{project_id}/files", tags=["files"])

# GET /api/projects/{project_id}/files - ファイル一覧取得
# GET /api/projects/{project_id}/files/{file_id} - ファイル詳細取得
# POST /api/projects/{project_id}/files - ファイル追加
# DELETE /api/projects/{project_id}/files/{file_id} - ファイル削除

@router.post("/diff-scan", response_model=DiffScanResponse)
async def scan_file_diff(
    project_id: int = Path(...),
    project: Project = Depends(get_project_by_id),
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> DiffScanResponse:
    """ファイルシステムとDBの差分をスキャン"""
    db_files = {row["file_path"]: row for row in list_all_documents(project_db)}
    fs_files = {}

    doc_root = Path(project.doc_root)
    if doc_root.exists():
        for file_path in doc_root.rglob("*.txt"):
            rel_path = str(file_path.relative_to(doc_root))
            fs_files[rel_path] = _compute_file_hash(file_path)

    added = [path for path in fs_files if path not in db_files]
    deleted = [path for path in db_files if path not in fs_files]
    modified = [
        path for path in fs_files
        if path in db_files and fs_files[path] != db_files[path]["content_hash"]
    ]

    return DiffScanResponse(added=added, modified=modified, deleted=deleted)
```

**diff-scanのロジック:**
- ファイルシステム上の `.txt` ファイルをスキャン
- SHA256ハッシュで変更を検出
- added / modified / deleted を返却

#### middleware/request_id.py (リクエストIDミドルウェア)
```python
from starlette.middleware.base import BaseHTTPMiddleware

class RequestIDMiddleware(BaseHTTPMiddleware):
    """すべてのレスポンスにX-Request-IDヘッダーを付与"""
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
```

#### middleware/logging.py (構造化ログミドルウェア)
```python
class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """リクエスト/レスポンスを構造化ログとして出力"""
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time

        logger.info("HTTP request", extra={
            "request_id": getattr(request.state, "request_id", None),
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration": duration,
        })
        return response
```

#### dependencies.py (依存性注入)
```python
import os
import sqlite3
from pathlib import Path
from typing import Generator

from fastapi import Depends, HTTPException

from genglossary.config import Config
from genglossary.db.connection import get_connection
from genglossary.db.project_repository import get_project
from genglossary.db.registry_schema import initialize_registry
from genglossary.models.project import Project


def get_config() -> Config:
    """Get application configuration.

    Returns:
        Config: Application configuration instance
    """
    return Config()


def get_registry_db(
    registry_path: str | None = None,
) -> Generator[sqlite3.Connection, None, None]:
    """Get registry database connection.

    Args:
        registry_path: Optional path to registry database.
            If None, uses GENGLOSSARY_REGISTRY_PATH env var or default.

    Yields:
        sqlite3.Connection: Registry database connection.
    """
    if registry_path is None:
        registry_path = os.getenv(
            "GENGLOSSARY_REGISTRY_PATH",
            str(Path.home() / ".genglossary" / "registry.db"),
        )

    conn = get_connection(registry_path)
    initialize_registry(conn)

    try:
        yield conn
    finally:
        conn.close()


def get_project_by_id(
    project_id: int,
    registry_conn: sqlite3.Connection = Depends(get_registry_db),
) -> Project:
    """Get project by ID or raise 404.

    Args:
        project_id: Project ID to retrieve.
        registry_conn: Registry database connection.

    Returns:
        Project: The requested project.

    Raises:
        HTTPException: 404 if project not found.
    """
    project = get_project(registry_conn, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return project


def get_project_db(
    project: Project = Depends(get_project_by_id),
) -> Generator[sqlite3.Connection, None, None]:
    """Get project-specific database connection.

    Args:
        project: Project instance from get_project_by_id.

    Yields:
        sqlite3.Connection: Project database connection.
    """
    conn = get_connection(project.db_path)
    try:
        yield conn
    finally:
        conn.close()
```

**依存性注入のパターン:**
- `get_registry_db()` - レジストリDB接続をyieldするジェネレーター
- `get_project_by_id()` - プロジェクトIDからProjectを取得、存在しない場合は404
- `get_project_db()` - プロジェクト固有のDB接続を取得（`get_project_by_id`に依存）

**使用例:**
```python
@router.get("/{project_id}/terms")
async def list_terms(
    project_id: int = Path(...),
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> list[TermResponse]:
    rows = list_all_terms(project_db)
    return TermResponse.from_db_rows(rows)
```

### 7. CLI層

#### cli.py (メインコマンド)
```python
import click

@click.command()
@click.argument("input_file")
@click.option("--output", "-o", default="output/glossary.md")
def main(input_file: str, output: str) -> None:
    """用語集を生成するCLIコマンド"""
    # 1. ドキュメント読み込み
    document = load_document(input_file)

    # 2. LLMクライアント初期化
    llm_client = OllamaClient()

    # 3. 用語抽出
    extractor = TermExtractor(llm_client)
    terms = extractor.extract(document)

    # 4. 用語集生成
    generator = GlossaryGenerator(llm_client)
    glossary = generator.generate(terms, document)

    # 5. 精査
    reviewer = GlossaryReviewer(llm_client)
    issues = reviewer.review(glossary)

    # 6. 改善
    refiner = GlossaryRefiner(llm_client)
    refined_glossary = refiner.refine(glossary, issues, document)

    # 7. 出力
    write_glossary(refined_glossary, output)
```

#### cli_db.py (DBサブコマンド)
```python
import click

@click.group()
def db() -> None:
    """Database management commands."""
    pass

@db.command("info")
@click.option("--db-path", default="./genglossary.db")
def info(db_path: str) -> None:
    """メタデータを表示"""
    conn = get_connection(db_path)
    metadata = get_metadata(conn)
    # Rich tableで表示
    ...

@db.group()
def terms() -> None:
    """抽出用語の管理コマンド"""
    pass

@terms.command("list")
@click.option("--db-path", default="./genglossary.db")
def terms_list(db_path: str) -> None:
    """用語一覧を表示（run_id不要）"""
    conn = get_connection(db_path)
    term_list = list_all_terms(conn)
    # Rich tableで表示
    ...

# provisional, refined コマンド群も同様（run_id削除）
```

**利用可能なDBコマンド (Schema v2):**
- `genglossary db init` - DB初期化
- `genglossary db info` - メタデータ表示
- `genglossary db terms list/show/update/delete/import/regenerate` - 用語管理
- `genglossary db provisional list/show/update/regenerate` - 暫定用語集管理
- `genglossary db issues list/regenerate` - 問題点管理
- `genglossary db refined list/show/update/export-md/regenerate` - 最終用語集管理

#### cli_api.py (APIサブコマンド)
```python
import click
import uvicorn

@click.group()
def api() -> None:
    """API server commands."""
    pass

@api.command()
@click.option("--host", default="127.0.0.1")
@click.option("--port", default=8000)
@click.option("--reload", is_flag=True)
def serve(host: str, port: int, reload: bool) -> None:
    """FastAPIサーバーを起動"""
    uvicorn.run(
        "genglossary.api.app:create_app",
        host=host,
        port=port,
        reload=reload,
        factory=True,
    )
```

**利用可能なAPIコマンド:**
- `genglossary api serve` - FastAPIサーバー起動
- `genglossary api serve --reload` - 開発モード（自動リロード）
- `genglossary api serve --host 0.0.0.0 --port 3000` - カスタムホスト/ポート

**APIエンドポイント:**

**システムエンドポイント:**
- `GET /health` - ヘルスチェック
- `GET /version` - バージョン情報
- `GET /docs` - OpenAPI ドキュメント（Swagger UI）
- `GET /redoc` - ReDoc ドキュメント

**Terms API (抽出用語の管理) - 5エンドポイント:**
- `GET /api/projects/{project_id}/terms` - 用語一覧取得
- `GET /api/projects/{project_id}/terms/{term_id}` - 用語詳細取得
- `POST /api/projects/{project_id}/terms` - 用語作成
- `PATCH /api/projects/{project_id}/terms/{term_id}` - 用語更新
- `DELETE /api/projects/{project_id}/terms/{term_id}` - 用語削除

**Provisional API (暫定用語集) - 5エンドポイント:**
- `GET /api/projects/{project_id}/provisional` - 暫定用語集一覧取得
- `GET /api/projects/{project_id}/provisional/{entry_id}` - 暫定用語詳細取得
- `PATCH /api/projects/{project_id}/provisional/{entry_id}` - 暫定用語更新（定義・confidence編集）
- `DELETE /api/projects/{project_id}/provisional/{entry_id}` - 暫定用語削除
- `POST /api/projects/{project_id}/provisional/{entry_id}/regenerate` - 単一エントリの再生成（LLM）

**Issues API (精査結果) - 2エンドポイント:**
- `GET /api/projects/{project_id}/issues` - 精査結果一覧取得（`issue_type` クエリパラメータでフィルタ可能）
- `GET /api/projects/{project_id}/issues/{issue_id}` - 精査結果詳細取得

**Refined API (最終用語集) - 5エンドポイント:**
- `GET /api/projects/{project_id}/refined` - 最終用語集一覧取得
- `GET /api/projects/{project_id}/refined/{term_id}` - 最終用語詳細取得
- `GET /api/projects/{project_id}/refined/export-md` - Markdownエクスポート
- `PATCH /api/projects/{project_id}/refined/{term_id}` - 最終用語更新
- `DELETE /api/projects/{project_id}/refined/{term_id}` - 最終用語削除

**Files API (ドキュメント管理) - 5エンドポイント:**
- `GET /api/projects/{project_id}/files` - ファイル一覧取得
- `GET /api/projects/{project_id}/files/{file_id}` - ファイル詳細取得
- `POST /api/projects/{project_id}/files` - ファイル追加
- `DELETE /api/projects/{project_id}/files/{file_id}` - ファイル削除
- `POST /api/projects/{project_id}/files/diff-scan` - ファイルシステムとDBの差分スキャン

**合計: 27エンドポイント** (システム4 + データAPI 22 + Projects API 1)

#### API実装のポイント

**1. SQLiteスレッド安全性**

FastAPIは非同期処理で複数のスレッドを使用するため、SQLite接続時に `check_same_thread=False` を指定しています。

```python
# db/connection.py
def get_connection(db_path: str) -> sqlite3.Connection:
    """Get database connection."""
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
```

**2. 依存性注入の階層化**

プロジェクト固有のDB接続は、レジストリDB接続とプロジェクト取得に依存する3段階の依存関係を構成しています。

```
get_registry_db()
    ↓ Depends
get_project_by_id(registry_conn)
    ↓ Depends
get_project_db(project)
```

**3. スキーマのファクトリーメソッド**

全てのレスポンススキーマに `from_db_row()` / `from_db_rows()` クラスメソッドを実装し、DB行からモデルへの変換ロジックを統一しています。

```python
class TermResponse(BaseModel):
    @classmethod
    def from_db_row(cls, row: Any) -> "TermResponse":
        """Create from database row."""
        return cls(
            id=row["id"],
            term_text=row["term_text"],
            category=row["category"],
        )

    @classmethod
    def from_db_rows(cls, rows: list[Any]) -> list["TermResponse"]:
        """Create list from database rows."""
        return [cls.from_db_row(row) for row in rows]
```

**4. 型注釈の工夫**

DB行の型は `sqlite3.Row` と `TypedDict` (GlossaryTermRow) の両方があるため、`from_db_row()` のパラメータ型には `Any` を使用しています。

**5. ルーティング順序**

FastAPIは定義順にルートをマッチングするため、`/export-md` のような固定パスは `/{term_id}` のようなパス パラメータより先に定義する必要があります。

```python
# refined.py
@router.get("/export-md", ...)  # 先に定義
async def export_markdown(...):
    ...

@router.get("/{term_id}", ...)  # 後に定義
async def get_refined_by_id(...):
    ...
```

**6. リクエストボディのアノテーション**

FastAPIでは、パスパラメータとリクエストボディを組み合わせる場合、明示的に `Body()` アノテーションが必要です。

```python
async def create_new_term(
    project_id: int = Path(...),           # パスパラメータ
    request: TermCreateRequest = Body(...), # リクエストボディ（明示的）
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> TermResponse:
    ...
```

**7. HTTPステータスコード**

RESTful APIの慣習に従ったステータスコードを返却しています。

- `200 OK` - GETリクエストの成功、PATCH/PUTの成功
- `201 Created` - POSTでリソース作成成功
- `204 No Content` - DELETEでリソース削除成功
- `404 Not Found` - リソースが見つからない（`get_project_by_id` が自動的に返却）

**regenerateコマンド群:**

各ステップのデータを再生成するコマンド。既存データを削除してから新規生成する。

```python
# 1. 用語抽出の再生成
@terms.command("regenerate")
@click.option("--input", required=True, help="入力ディレクトリ")
@click.option("--llm-provider", default="ollama")
@click.option("--model", default=None)
@click.option("--db-path", default="./genglossary.db")
def terms_regenerate(input: str, llm_provider: str, model: str | None, db_path: str):
    """ドキュメントから用語を再抽出

    処理フロー:
    1. 既存用語を全削除（delete_all_terms）
    2. ドキュメント読み込み（DocumentLoader）
    3. LLMで用語抽出（TermExtractor）
    4. DBに保存（create_term）
    """
    ...

# 2. 暫定用語集の再生成
@provisional.command("regenerate")
@click.option("--llm-provider", default="ollama")
@click.option("--model", default=None)
@click.option("--db-path", default="./genglossary.db")
def provisional_regenerate(llm_provider: str, model: str | None, db_path: str):
    """抽出済み用語から暫定用語集を再生成

    処理フロー:
    1. 既存暫定用語を全削除（delete_all_provisional）
    2. DBから用語とドキュメントを取得
    3. ドキュメントをファイルから再構築
    4. LLMで用語集生成（GlossaryGenerator）
    5. DBに保存（create_provisional_term）
    """
    ...

# 3. 問題点の再生成
@issues.command("regenerate")
@click.option("--llm-provider", default="ollama")
@click.option("--model", default=None)
@click.option("--db-path", default="./genglossary.db")
def issues_regenerate(llm_provider: str, model: str | None, db_path: str):
    """暫定用語集を精査して問題点を再生成

    処理フロー:
    1. 既存問題を全削除（delete_all_issues）
    2. DBから暫定用語集を取得
    3. Glossaryオブジェクトを再構築
    4. LLMで精査（GlossaryReviewer）
    5. DBに保存（create_issue）
    """
    ...

# 4. 最終用語集の再生成
@refined.command("regenerate")
@click.option("--llm-provider", default="ollama")
@click.option("--model", default=None)
@click.option("--db-path", default="./genglossary.db")
def refined_regenerate(llm_provider: str, model: str | None, db_path: str):
    """問題点に基づいて用語集を改善し最終版を再生成

    処理フロー:
    1. 既存最終用語を全削除（delete_all_refined）
    2. DBから暫定用語集、問題点、ドキュメントを取得
    3. Glossary、Issue、Documentオブジェクトを再構築
    4. LLMで改善（GlossaryRefiner）
    5. DBに保存（create_refined_term）
    """
    ...
```

**オブジェクト再構築パターン:**

regenerateコマンドではDBから取得したデータを元のPydanticモデルに復元する必要がある。

```python
# Document再構築
documents: list[Document] = []
loader = DocumentLoader()
for doc_row in doc_rows:
    try:
        doc = loader.load_file(doc_row["file_path"])
        documents.append(doc)
    except FileNotFoundError:
        console.print(f"[yellow]警告: ファイルが見つかりません[/yellow]")
        continue

# Glossary再構築
from genglossary.models.term import Term
glossary = Glossary()
for prov_row in provisional_rows:
    term = Term(
        name=prov_row["term_name"],
        definition=prov_row["definition"],
        confidence=prov_row["confidence"],
        occurrences=prov_row["occurrences"],  # 既にdeserialize済み
    )
    glossary.add_term(term)

# GlossaryIssue再構築
from genglossary.models.glossary import GlossaryIssue
issues: list[GlossaryIssue] = []
for issue_row in issue_rows:
    issue = GlossaryIssue(
        term_name=issue_row["term_name"],
        issue_type=issue_row["issue_type"],
        description=issue_row["description"],
        # should_exclude/exclusion_reasonはDBに保存されていないためデフォルト値
    )
    issues.append(issue)
```

## データフロー

### 基本フロー (Markdown出力のみ、DBなし)

```
┌──────────────────┐
│  target_docs/    │ 入力ドキュメント
│  sample.txt      │
└────────┬─────────┘
         │ load_document()
         ↓
┌──────────────────┐
│    Document      │ ドキュメントモデル
└────────┬─────────┘
         │ extract_terms(return_categories=False)
         ↓
┌──────────────────┐
│   List[str]      │ 用語リスト (common_noun除外済み)
└────────┬─────────┘
         │ generate()
         ↓
┌──────────────────┐
│    Glossary      │ 暫定用語集
│  (provisional)   │
└────────┬─────────┘
         │ review()
         ↓
┌──────────────────┐
│ List[Issue]      │ 問題点リスト
└────────┬─────────┘
         │ refine()
         ↓
┌──────────────────┐
│    Glossary      │ 最終用語集
│   (refined)      │
└────────┬─────────┘
         │ write_glossary()
         ↓
┌──────────────────┐
│   output/        │ 出力ファイル
│   glossary.md    │
└──────────────────┘
```

### DB保存付きフロー (デフォルト、Schema v2)

```
┌──────────────────┐     ┌──────────────────┐
│  target_docs/    │────→│ DB: metadata     │
│  sample.txt      │     │  (id=1, input_   │
└────────┬─────────┘     │   path, llm_*)   │
         │                └──────────────────┘
         │ load_document()
         ↓
┌──────────────────┐     ┌──────────────────┐
│    Document      │────→│ DB: documents    │
└────────┬─────────┘     │  (run_id削除)    │
         │                └──────────────────┘
         │ extract(return_categories=True)
         ↓
┌──────────────────┐     ┌──────────────────┐
│List[Classified   │────→│ DB: terms_       │
│    Term]         │     │     extracted    │
│ (カテゴリ付き)   │     │  + category列    │
│ ※common_noun含む │     │  (run_id削除)    │
└────────┬─────────┘     └──────────────────┘
         │ generate(skip_common_nouns=True)
         ↓             ※common_nounをスキップ
┌──────────────────┐     ┌──────────────────┐
│    Glossary      │────→│ DB: glossary_    │
│  (provisional)   │     │     provisional  │
└────────┬─────────┘     │  (run_id削除)    │
         │                └──────────────────┘
         │ review()
         ↓
┌──────────────────┐     ┌──────────────────┐
│ List[Issue]      │────→│ DB: glossary_    │
│  問題点リスト    │     │     issues       │
└────────┬─────────┘     │  (run_id削除)    │
         │                └──────────────────┘
         │ refine()
         ↓
┌──────────────────┐     ┌──────────────────┐
│    Glossary      │────→│ DB: glossary_    │
│   (refined)      │     │     refined      │
└────────┬─────────┘     │  (run_id削除)    │
         │                └──────────────────┘
         │ write_glossary()
         ↓
┌──────────────────┐
│   output/        │ Markdown出力
│   glossary.md    │
└──────────────────┘

         ↓ DB CLIで操作可能（run_id不要）
┌──────────────────┐
│ genglossary db   │
│ - info           │
│ - terms list     │
│ - provisional    │
│ - refined        │
│   export-md      │
└──────────────────┘
```

### カテゴリ分類フロー (TermExtractor内部処理)

用語抽出は2段階のLLM処理で行われます：

```
1. SudachiPy形態素解析
   ↓ 固有名詞・複合名詞を抽出

2. LLM分類 (バッチ処理)
   ↓ 6カテゴリに分類

   - person_name (人名)
   - place_name (地名)
   - organization (組織・団体)
   - title (役職・称号)
   - technical_term (専門用語)
   - common_noun (一般名詞) ← 除外対象

3. 結果の返却
   - return_categories=False: common_noun除外 → list[str]
   - return_categories=True: 全カテゴリ含む → list[ClassifiedTerm]
```

**DB保存時の動作:**
- `return_categories=True` でカテゴリ付き抽出
- 全カテゴリ（common_noun含む）をDBの `terms_extracted` テーブルに保存
- 用語集生成時に `skip_common_nouns=True` で common_noun をフィルタ
- 既存データ（category=NULL）は common_noun として扱う

**後方互換性:**
- DBなしモード: `return_categories=False` で既存動作を維持
- 既存の `list[str]` を期待するコードはそのまま動作

## import文の例

### ✅ 良いimport

```python
# 標準ライブラリは先頭
import sys
from pathlib import Path

# サードパーティは次
import httpx
from pydantic import BaseModel

# 自プロジェクトは最後
# モデルのimport
from genglossary.models.document import Document
from genglossary.models.term import (
    Term,
    TermOccurrence,
    ClassifiedTerm,
    TermCategory,
)
from genglossary.models.glossary import Glossary, GlossaryIssue

# LLMクライアントのimport
from genglossary.llm.base import BaseLLMClient
from genglossary.llm.ollama_client import OllamaClient

# DB層のimport (Schema v2)
from genglossary.db.connection import get_connection
from genglossary.db.schema import initialize_db
from genglossary.db.metadata_repository import get_metadata, upsert_metadata
from genglossary.db.term_repository import create_term, list_all_terms, delete_all_terms
from genglossary.db.provisional_repository import (
    create_provisional_term,
    list_all_provisional,
    delete_all_provisional,
)
from genglossary.db.refined_repository import (
    create_refined_term,
    list_all_refined,
    delete_all_refined,
)

# 処理レイヤーのimport
from genglossary.term_extractor import TermExtractor
from genglossary.glossary_generator import GlossaryGenerator
```

### ❌ 悪いimport

```python
# ワイルドカードインポート（避ける）
from genglossary.models import *

# 相対インポート（避ける）
from ..models.document import Document

# 循環インポート（絶対に避ける）
# term.py で glossary をimport、glossary.py で term をimport
```

## モジュール分割の判断基準

### 新しいクラス/関数を作る基準

1. **責務が明確に異なる**: 用語抽出と用語集生成は別クラス
2. **テストの独立性**: 独立してテスト可能な単位
3. **再利用性**: 他の場所でも使う可能性がある

### 例: morphological_analyzer.py を追加すべきか？

```python
# ✅ 分離すべき（責務が異なる）
class MorphologicalAnalyzer:
    """形態素解析を行うクラス（janomeを使用）"""
    def analyze(self, text: str) -> list[Token]:
        ...

class TermExtractor:
    """用語抽出を行うクラス（形態素解析を使用）"""
    def __init__(self, analyzer: MorphologicalAnalyzer, llm_client: BaseLLMClient):
        self.analyzer = analyzer
        self.llm_client = llm_client
```

```python
# ❌ 1つにまとめない（責務が混在）
class TermExtractor:
    """用語抽出と形態素解析を両方行う"""
    def analyze(self, text: str) -> list[Token]:  # 形態素解析
        ...

    def extract(self, document: Document) -> list[str]:  # 用語抽出
        ...
```

## 依存関係の原則

### レイヤー間の依存方向

```
┌──────────────┐
│   CLI層      │ (cli.py, cli_db.py, cli_api.py)
│   API層      │ (api/app.py, routers/, middleware/)
└────┬─────────┘
     │ depends on
     ├─────────────────────────┐
     ↓                         ↓
┌──────────────┐          ┌──────────────┐
│  処理層      │          │   DB層       │
│ (Extractor,  │          │ (repositories│
│  Generator,  │          │  schema,     │
│  Reviewer,   │          │  connection) │
│  Refiner)    │          └────┬─────────┘
└────┬─────────┘               │
     │ depends on              │
     ↓                         │
┌──────────────┐               │
│   LLM層      │               │
│ (BaseLLM,    │               │
│  OllamaClient│               │
└────┬─────────┘               │
     │ depends on              │
     ↓                         ↓
┌──────────────────────────────┐
│        モデル層              │
│ (Document, Term, Glossary,   │
│  TermOccurrence)             │
└──────────────────────────────┘
```

**原則**:
- 上位レイヤーは下位レイヤーに依存できるが、逆は不可
- CLI層は処理層とDB層の両方に依存可能
- DB層はモデル層にのみ依存（処理層には依存しない）
- 処理層はDB層を意識しない（疎結合）

### ✅ 良い依存関係

```python
# TermExtractor（処理層）→ Document（モデル層）
class TermExtractor:
    def extract(self, document: Document) -> list[str]:
        ...
```

### ❌ 悪い依存関係

```python
# Document（モデル層）→ TermExtractor（処理層）
class Document(BaseModel):
    def extract_terms(self) -> list[str]:
        extractor = TermExtractor()  # ❌ 下位が上位に依存
        return extractor.extract(self)
```

## 関連ドキュメント

- [プロジェクト概要](@.claude/rules/00-overview.md) - 4ステップフロー、技術スタック
- LLM統合 → `/llm-integration` スキルを使用
- データベース機能 → README.md「データベース機能 (SQLite)」セクション参照

## データベース設計の原則

### Repository パターン
- 各テーブルに対して専用のrepositoryモジュールを作成
- CRUD操作を関数として実装（クラス化せず、シンプルに）
- 接続管理はrepositoryの外で行う（呼び出し元の責任）

### トランザクション管理
- 各repository関数は`conn.commit()`を実行
- エラー時のロールバックは呼び出し元で処理
- 複数のrepository操作をまとめる場合はCLI層でトランザクション管理

### 型安全性
- `sqlite3.Row`を使用してカラム名でアクセス
- TypedDictで型ヒントを提供（`GlossaryTermRow`など）
- JSONシリアライズは専用関数で統一（`serialize_occurrences`など）
