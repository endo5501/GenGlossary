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
│   ├── document_loader.py        # ドキュメント読み込み
│   ├── term_extractor.py         # ステップ1: 用語抽出
│   ├── glossary_generator.py     # ステップ2: 用語集生成
│   ├── glossary_reviewer.py      # ステップ3: 精査
│   ├── glossary_refiner.py       # ステップ4: 改善
│   ├── output/
│   │   ├── __init__.py
│   │   └── markdown_writer.py    # Markdown出力
│   ├── config.py                 # 設定管理
│   └── cli.py                    # CLIエントリーポイント
├── tests/                        # テストコード
│   ├── models/
│   │   ├── test_document.py
│   │   ├── test_term.py
│   │   └── test_glossary.py
│   ├── llm/
│   │   ├── test_base.py
│   │   └── test_ollama_client.py
│   ├── test_document_loader.py
│   ├── test_term_extractor.py
│   ├── test_glossary_generator.py
│   ├── test_glossary_reviewer.py
│   ├── test_glossary_refiner.py
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

### 3. 処理レイヤー

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

### 4. output/ - 出力層

#### markdown_writer.py
```python
def write_glossary(glossary: Glossary, output_path: str) -> None:
    """用語集をMarkdown形式で出力"""
    ...
```

### 5. CLI層

#### cli.py
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

## データフロー

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

## import文の例

### ✅ 良いimport

```python
# モデルのimport
from genglossary.models.document import Document
from genglossary.models.term import Term, TermOccurrence
from genglossary.models.glossary import Glossary, GlossaryIssue

# LLMクライアントのimport
from genglossary.llm.base import BaseLLMClient
from genglossary.llm.ollama_client import OllamaClient

# 処理レイヤーのimport
from genglossary.term_extractor import TermExtractor
from genglossary.glossary_generator import GlossaryGenerator

# 標準ライブラリは先頭
import sys
from pathlib import Path

# サードパーティは次
import httpx
from pydantic import BaseModel

# 自プロジェクトは最後
from genglossary.models.document import Document
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
┌──────────┐
│   CLI    │
└────┬─────┘
     │ depends on
     ↓
┌──────────┐
│ 処理層   │ (Extractor, Generator, Reviewer, Refiner)
└────┬─────┘
     │ depends on
     ↓
┌──────────┐
│ LLM層    │ (BaseLLMClient, OllamaClient)
└────┬─────┘
     │ depends on
     ↓
┌──────────┐
│ モデル層 │ (Document, Term, Glossary)
└──────────┘
```

**原則**: 上位レイヤーは下位レイヤーに依存できるが、逆は不可

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
- [LLM統合](@.claude/rules/04-llm-integration.md) - Ollama連携の詳細
