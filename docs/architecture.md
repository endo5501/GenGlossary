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
│   │   └── glossary.py          # Glossary, GlossaryIssue
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
│   │   └── refined_repository.py     # 最終用語集CRUD
│   ├── document_loader.py        # ドキュメント読み込み
│   ├── term_extractor.py         # ステップ1: 用語抽出
│   ├── glossary_generator.py     # ステップ2: 用語集生成
│   ├── glossary_reviewer.py      # ステップ3: 精査
│   ├── glossary_refiner.py       # ステップ4: 改善
│   ├── output/
│   │   ├── __init__.py
│   │   └── markdown_writer.py    # Markdown出力
│   ├── config.py                 # 設定管理
│   ├── cli.py                    # CLIエントリーポイント (generate)
│   └── cli_db.py                 # DB管理CLI (db サブコマンド)
├── tests/                        # テストコード
│   ├── models/
│   │   ├── test_document.py
│   │   ├── test_term.py
│   │   └── test_glossary.py
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
│   │   └── test_refined_repository.py
│   ├── test_document_loader.py
│   ├── test_term_extractor.py
│   ├── test_glossary_generator.py
│   ├── test_glossary_reviewer.py
│   ├── test_glossary_refiner.py
│   ├── test_cli_db.py           # DB CLI統合テスト
│   ├── test_cli_db_regenerate.py # regenerateコマンドテスト
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
class Term(BaseModel):
    """用語を表すモデル"""
    text: str
    definition: str
    occurrences: list[TermOccurrence]

class TermOccurrence(BaseModel):
    """用語の出現箇所"""
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
class TermExtractor:
    """用語抽出を行うクラス"""

    def __init__(self, llm_client: BaseLLMClient):
        self.llm_client = llm_client

    def extract(self, document: Document) -> list[str]:
        """ドキュメントから用語を抽出"""
        prompt = self._build_prompt(document)
        response = self.llm_client.generate(prompt)
        return self._parse_response(response)
```

#### glossary_generator.py (ステップ2)
```python
class GlossaryGenerator:
    """用語集生成を行うクラス"""

    def __init__(self, llm_client: BaseLLMClient):
        self.llm_client = llm_client

    def generate(self, terms: list[str], document: Document) -> Glossary:
        """用語集を生成"""
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

### 6. CLI層

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

@db.command("metadata")
@click.option("--db-path", default="./genglossary.db")
def metadata_show(db_path: str) -> None:
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

### 基本フロー (Markdown出力のみ)

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
         │ extract()
         ↓
┌──────────────────┐
│   List[str]      │ 用語リスト
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

### DB保存付きフロー (--db-path指定時、Schema v2)

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
         │ extract()
         ↓
┌──────────────────┐     ┌──────────────────┐
│   List[str]      │────→│ DB: terms_       │
│   用語リスト     │     │     extracted    │
└────────┬─────────┘     │  (run_id削除)    │
         │                └──────────────────┘
         │ generate()
         ↓
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
│ - metadata       │
│ - terms list     │
│ - provisional    │
│ - refined        │
│   export-md      │
└──────────────────┘
```

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
from genglossary.models.term import Term, TermOccurrence
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
│   CLI層      │ (cli.py, cli_db.py)
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
