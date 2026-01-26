# 設計原則

## import文の例

### 良いimport

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

### 悪いimport

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

**分離すべき（責務が異なる）:**
```python
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

**1つにまとめない（責務が混在）:**
```python
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

### 良い依存関係

```python
# TermExtractor（処理層）→ Document（モデル層）
class TermExtractor:
    def extract(self, document: Document) -> list[str]:
        ...
```

### 悪い依存関係

```python
# Document（モデル層）→ TermExtractor（処理層）
class Document(BaseModel):
    def extract_terms(self) -> list[str]:
        extractor = TermExtractor()  # 下位が上位に依存
        return extractor.extract(self)
```
