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
│   │   └── ollama_client.py     # OllamaClient
│   ├── db/                       # データベース層
│   │   ├── __init__.py
│   │   ├── connection.py        # SQLite接続管理
│   │   ├── schema.py            # スキーマ定義・初期化
│   │   ├── models.py            # DB用TypedDict・シリアライズ
│   │   ├── run_repository.py    # 実行履歴CRUD
│   │   ├── document_repository.py    # ドキュメントCRUD
│   │   ├── term_repository.py   # 抽出用語CRUD
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
│   │   ├── test_run_repository.py
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

### 3. db/ - データベース層

**役割**: SQLiteへのデータ永続化とCRUD操作

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
    """データベーススキーマを初期化"""
    # テーブル作成: runs, documents, terms_extracted,
    # glossary_provisional, glossary_issues, glossary_refined
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
    """用語集テーブル共通型 (provisional/refined)"""
    id: int
    run_id: int
    term_name: str
    definition: str
    confidence: float
    occurrences: list[TermOccurrence]

def serialize_occurrences(occurrences: list[TermOccurrence]) -> str:
    """TermOccurrenceをJSON文字列に変換"""
    ...

def deserialize_occurrences(json_str: str) -> list[TermOccurrence]:
    """JSON文字列をTermOccurrenceに変換"""
    ...
```

#### run_repository.py
```python
def create_run(
    conn: sqlite3.Connection,
    input_path: str,
    llm_provider: str,
    llm_model: str
) -> int:
    """実行履歴を作成し、run_idを返す"""
    ...

def list_runs(conn: sqlite3.Connection, limit: int = 20) -> list[sqlite3.Row]:
    """実行履歴一覧を取得"""
    ...
```

#### term_repository.py
```python
def create_term(
    conn: sqlite3.Connection,
    run_id: int,
    term_text: str,
    category: str | None = None
) -> int:
    """抽出用語を作成"""
    ...

def update_term(
    conn: sqlite3.Connection,
    term_id: int,
    term_text: str,
    category: str | None = None
) -> None:
    """用語を更新"""
    ...

def delete_term(conn: sqlite3.Connection, term_id: int) -> None:
    """用語を削除"""
    ...
```

#### provisional_repository.py / refined_repository.py
```python
def create_provisional_term(
    conn: sqlite3.Connection,
    run_id: int,
    term_name: str,
    definition: str,
    confidence: float,
    occurrences: list[TermOccurrence]
) -> int:
    """暫定用語集エントリを作成"""
    ...

def update_provisional_term(
    conn: sqlite3.Connection,
    term_id: int,
    definition: str,
    confidence: float
) -> None:
    """暫定用語を更新"""
    ...
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

@db.group()
def runs() -> None:
    """実行履歴の管理コマンド"""
    pass

@runs.command("list")
@click.option("--db-path", default="./genglossary.db")
def runs_list(db_path: str) -> None:
    """実行履歴一覧を表示"""
    conn = get_connection(db_path)
    run_list = list_runs(conn)
    # Rich tableで表示
    ...

@db.group()
def terms() -> None:
    """抽出用語の管理コマンド"""
    pass

@terms.command("list")
@click.option("--run-id", type=int, required=True)
def terms_list(run_id: int, db_path: str) -> None:
    """用語一覧を表示"""
    ...

# provisional, refined コマンド群も同様
```

**利用可能なDBコマンド:**
- `genglossary db init` - DB初期化
- `genglossary db runs list/show/latest` - 実行履歴管理
- `genglossary db terms list/show/update/delete/import` - 用語管理
- `genglossary db provisional list/show/update` - 暫定用語集管理
- `genglossary db refined list/show/update/export-md` - 最終用語集管理

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

### DB保存付きフロー (--db-path指定時)

```
┌──────────────────┐
│  target_docs/    │ 入力ドキュメント
│  sample.txt      │
└────────┬─────────┘
         │ load_document()
         ↓
┌──────────────────┐     ┌──────────────────┐
│    Document      │────→│ DB: documents    │
└────────┬─────────┘     └──────────────────┘
         │ extract()
         ↓
┌──────────────────┐     ┌──────────────────┐
│   List[str]      │────→│ DB: terms_       │
│   用語リスト     │     │     extracted    │
└────────┬─────────┘     └──────────────────┘
         │ generate()
         ↓
┌──────────────────┐     ┌──────────────────┐
│    Glossary      │────→│ DB: glossary_    │
│  (provisional)   │     │     provisional  │
└────────┬─────────┘     └──────────────────┘
         │ review()
         ↓
┌──────────────────┐     ┌──────────────────┐
│ List[Issue]      │────→│ DB: glossary_    │
│  問題点リスト    │     │     issues       │
└────────┬─────────┘     └──────────────────┘
         │ refine()
         ↓
┌──────────────────┐     ┌──────────────────┐
│    Glossary      │────→│ DB: glossary_    │
│   (refined)      │     │     refined      │
└────────┬─────────┘     └──────────────────┘
         │ write_glossary()
         ↓
┌──────────────────┐
│   output/        │ Markdown出力
│   glossary.md    │
└──────────────────┘

         ↓ DB CLIで操作可能
┌──────────────────┐
│ genglossary db   │
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

# DB層のimport
from genglossary.db.connection import get_connection
from genglossary.db.schema import initialize_db
from genglossary.db.term_repository import create_term, list_terms_by_run
from genglossary.db.provisional_repository import create_provisional_term

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
