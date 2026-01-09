---
name: code-style
description: "Python code style guide for GenGlossary project. Covers naming conventions (PascalCase classes, snake_case functions/variables), type hints, Google-style docstrings, import ordering, and Pydantic model patterns. Use when: (1) Writing new code, (2) Reviewing code style, (3) Naming classes/functions/variables, (4) Adding type hints, (5) Writing docstrings."
---

# Code Style Guide

GenGlossaryプロジェクトのコードスタイル、命名規則、型ヒント、docstring規約のガイドです。

## 命名規則

### クラス名: PascalCase

```python
# ✅ 良い例
class Document:
    pass

class TermExtractor:
    pass

class OllamaClient:
    pass

# ❌ 悪い例
class document:  # 小文字始まり
    pass

class term_extractor:  # スネークケース
    pass

class ollamaClient:  # キャメルケース
    pass
```

### 関数・メソッド名: snake_case

```python
# ✅ 良い例
def load_document(file_path: str) -> Document:
    ...

def get_line(self, line_number: int) -> str:
    ...

def extract_terms(self, document: Document) -> list[str]:
    ...

# ❌ 悪い例
def LoadDocument(file_path: str):  # PascalCase
    ...

def getLine(self, lineNumber: int):  # キャメルケース
    ...

def ExtractTerms(self, document: Document):  # PascalCase
    ...
```

### 変数名: snake_case

```python
# ✅ 良い例
file_path = "/path/to/file.txt"
line_number = 10
term_list = ["用語1", "用語2"]

# ❌ 悪い例
filePath = "/path/to/file.txt"  # キャメルケース
LineNumber = 10  # PascalCase
termList = ["用語1", "用語2"]  # キャメルケース
```

### 定数: UPPER_SNAKE_CASE

```python
# ✅ 良い例
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30.0
OLLAMA_BASE_URL = "http://localhost:11434"

# ❌ 悪い例
max_retries = 3  # 小文字
MaxRetries = 3  # PascalCase
```

### プライベートメソッド: _snake_case

```python
class OllamaClient:
    def generate(self, prompt: str) -> str:
        """Public method."""
        ...

    def _request_with_retry(self, url: str, payload: dict) -> httpx.Response:
        """Private method with underscore prefix."""
        ...

    def _parse_json_response(self, text: str) -> dict:
        """Private method with underscore prefix."""
        ...
```

## 型ヒント

**必須**: すべての関数・メソッドに型ヒントを付ける

### ✅ 良い例

```python
from typing import Type, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

class Document(BaseModel):
    file_path: str
    content: str

def load_document(file_path: str) -> Document:
    """Load a document from file path."""
    ...

def get_line(self, line_number: int) -> str:
    """Get a specific line by line number."""
    ...

def extract_terms(self, document: Document) -> list[str]:
    """Extract terms from document."""
    ...

def generate_structured(
    self,
    prompt: str,
    response_model: Type[T],
    max_retries: int = 3
) -> T:
    """Generate structured output."""
    ...
```

**ポイント**:
- ✅ 引数の型を明示
- ✅ 戻り値の型を明示
- ✅ ジェネリック型（Type[T]）を適切に使用
- ✅ デフォルト引数も型ヒント付き

### ❌ 悪い例

```python
# 型ヒントなし
def load_document(file_path):
    ...

# 戻り値の型ヒントなし
def get_line(self, line_number: int):
    ...

# Noneを返すのに型ヒントなし
def write_glossary(glossary, output_path):
    ...
```

### None を返す場合

```python
# ✅ 良い例
def write_glossary(glossary: Glossary, output_path: str) -> None:
    """Write glossary to file."""
    ...

# ✅ Optional型の使用
from typing import Optional

def find_term(self, term_text: str) -> Optional[Term]:
    """Find a term, return None if not found."""
    ...
```

## Docstring規約

**スタイル**: Google style

### クラスのdocstring

```python
class Document(BaseModel):
    """Represents a loaded document with its content and metadata.

    Attributes:
        file_path: The path to the source file.
        content: The full text content of the document.
    """

    file_path: str
    content: str
```

### 関数・メソッドのdocstring

```python
def get_context(self, line_number: int, context_lines: int = 1) -> list[str]:
    """Get a line with surrounding context.

    Args:
        line_number: The center line number (1-based index).
        context_lines: Number of lines to include before and after.

    Returns:
        A list of lines including the specified line and its context.

    Raises:
        IndexError: If line_number is out of range.
    """
    ...
```

**ポイント**:
- ✅ 1行目: 簡潔な説明（ピリオドで終わる）
- ✅ Args: 各引数の説明
- ✅ Returns: 戻り値の説明
- ✅ Raises: 例外の説明（該当する場合）

### ✅ 良いdocstring

```python
def _request_with_retry(self, url: str, payload: dict) -> httpx.Response:
    """Execute HTTP request with exponential backoff retry logic.

    Retries the request up to max_retries times with exponential backoff
    (1s, 2s, 4s) between attempts. Only retries on httpx.HTTPError.

    Args:
        url: The API endpoint URL.
        payload: The JSON payload to send.

    Returns:
        The HTTP response object.

    Raises:
        httpx.HTTPError: If all retries fail.
    """
    ...
```

**良い点**:
- ✅ 詳細な説明（リトライロジックの動作）
- ✅ 引数、戻り値、例外の説明が明確
- ✅ 実装の意図が理解できる

### ❌ 悪いdocstring

```python
def get_line(self, line_number):
    """Get line."""  # 曖昧、引数・戻り値の説明なし
    ...

def extract_terms(self, document):
    # docstringなし
    ...
```

## インポート

### インポートの順序

```python
# 1. 標準ライブラリ
import json
import re
import time
from pathlib import Path
from typing import Type, TypeVar

# 2. サードパーティライブラリ
import httpx
from pydantic import BaseModel, ValidationError

# 3. 自プロジェクト
from genglossary.models.document import Document
from genglossary.llm.base import BaseLLMClient
```

**ルール**:
1. 標準ライブラリ
2. サードパーティ
3. 自プロジェクト
4. 各グループ間は空行で分離

### ✅ 良いインポート

```python
# 明示的なインポート
from genglossary.models.document import Document
from genglossary.models.term import Term, TermOccurrence

# まとめてインポート（同じモジュールから）
from genglossary.llm.base import BaseLLMClient
from genglossary.llm.ollama_client import OllamaClient
```

### ❌ 悪いインポート

```python
# ワイルドカード（避ける）
from genglossary.models import *

# 未使用のインポート
import sys  # 使われていない
from pathlib import Path  # 使われていない
```

## コードフォーマット

### 行の長さ

- **最大**: 88文字（Blackのデフォルト）
- 長い行は適切に折り返す

```python
# ✅ 良い例（適切に折り返し）
def generate_structured(
    self,
    prompt: str,
    response_model: Type[T],
    max_retries: int = 3,
    timeout: float = 30.0
) -> T:
    ...

# ✅ 良い例（長い文字列）
error_message = (
    f"Failed to parse structured output after {max_retries} attempts. "
    f"Last response: {response_text[:100]}"
)
```

### インデント

- **スペース**: 4スペース（タブは使わない）

```python
# ✅ 良い例
class Document(BaseModel):
    file_path: str
    content: str

    def get_line(self, line_number: int) -> str:
        if line_number < 1:
            raise IndexError("Invalid line number")
        return self.lines[line_number - 1]
```

### 空行

```python
# ✅ 良い例

# トップレベルの定義の間: 2行空ける
class Document(BaseModel):
    ...


class Term(BaseModel):
    ...


# メソッドの間: 1行空ける
class OllamaClient:
    def generate(self, prompt: str) -> str:
        ...

    def generate_structured(self, prompt: str) -> BaseModel:
        ...

    def _request_with_retry(self, url: str) -> httpx.Response:
        ...
```

## ファイル構成

### モジュールファイルの構成

```python
"""Module docstring: OllamaClient implementation."""

# 1. インポート
import json
from typing import Type

import httpx
from pydantic import BaseModel

# 2. 定数
DEFAULT_TIMEOUT = 30.0
MAX_RETRIES = 3

# 3. 型エイリアス・TypeVar
T = TypeVar("T", bound=BaseModel)

# 4. クラス定義
class OllamaClient(BaseLLMClient):
    """Ollama LLM client."""

    def __init__(self, ...):
        ...

    # Publicメソッド
    def generate(self, prompt: str) -> str:
        ...

    # Privateメソッド
    def _request_with_retry(self, url: str) -> httpx.Response:
        ...

# 5. モジュールレベル関数（あれば）
def helper_function() -> None:
    ...
```

## Pydanticモデルのスタイル

### ✅ 良い例

```python
from pydantic import BaseModel, Field

class Term(BaseModel):
    """Represents a term in the glossary.

    Attributes:
        text: The term text.
        definition: The term definition.
        occurrences: List of term occurrences in the document.
    """

    text: str = Field(..., min_length=1, description="The term text")
    definition: str = Field(..., min_length=1, description="The term definition")
    occurrences: list[TermOccurrence] = Field(default_factory=list)

    class Config:
        """Pydantic model configuration."""
        frozen = False  # モデルが変更可能かどうか
```

### フィールドのバリデーション

```python
from pydantic import BaseModel, Field, field_validator

class Glossary(BaseModel):
    """Represents a glossary with terms."""

    terms: list[Term] = Field(default_factory=list, description="List of terms")

    @field_validator("terms")
    @classmethod
    def validate_terms_not_empty(cls, v: list[Term]) -> list[Term]:
        """Validate that terms list is not empty."""
        if not v:
            raise ValueError("Glossary must contain at least one term")
        return v
```

## クイックチェックリスト

### コーディング前
- [ ] クラス名はPascalCaseか
- [ ] 関数・変数名はsnake_caseか
- [ ] 定数はUPPER_SNAKE_CASEか

### コーディング中
- [ ] すべての関数に型ヒントを付けたか
- [ ] Docstringを書いたか（Google style）
- [ ] インポートの順序は正しいか（標準→サードパーティ→自プロジェクト）

### コーディング後
- [ ] 行の長さは88文字以内か
- [ ] インデントは4スペースか
- [ ] 適切な空行を入れたか（クラス間2行、メソッド間1行）
