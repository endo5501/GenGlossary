# モデル・処理・出力レイヤー

このドキュメントでは、データモデル層、LLMクライアント層、処理レイヤー、出力層について説明します。

## 1. models/ - データモデル層

**役割**: ドメインモデルの定義

### document.py
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

### term.py
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

### glossary.py
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

### project.py
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
    llm_provider: str        # LLMプロバイダー（ollama / openai）
    llm_model: str           # LLMモデル名
    llm_base_url: str        # LLMベースURL（OpenAI互換API用）
    created_at: datetime
    updated_at: datetime
    last_run_at: datetime | None
    status: ProjectStatus
```

## 2. llm/ - LLMクライアント層

**役割**: LLMとの通信を抽象化

### base.py
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

### ollama_client.py
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

### factory.py
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

## 3. 処理レイヤー

### document_loader.py
```python
class DocumentLoader:
    """ドキュメント読み込みとセキュリティバリデーション"""

    def __init__(
        self,
        supported_extensions: list[str] | None = None,  # デフォルト: [".txt", ".md"]
        max_file_size: int | None = 10 * 1024 * 1024,   # デフォルト: 10MB
        excluded_patterns: list[str] | None = None,     # デフォルト: セキュリティパターン
        validate_path: bool = True,                      # ディレクトリトラバーサル防止
    ):
        ...

    def load_file(self, path: str) -> Document: ...
    def load_directory(self, path: str) -> list[Document]: ...
    def load_documents(self, paths: list[str]) -> list[Document]: ...
```

**セキュリティ機能:**
- **ファイルサイズ制限**: 巨大ファイルによるリソース枯渇を防止
- **パス検証**: シンボリックリンクを解決してディレクトリトラバーサルを検出
- **機密ファイル除外**: `.env`, `*.key`, `*.pem`, `credentials*`, `.git*` 等を自動除外

**例外:**
- `FileSizeExceededError`: ファイルサイズ超過
- `PathTraversalError`: ディレクトリトラバーサル検出
- `ExcludedFileError`: 除外ファイルへのアクセス試行

### term_extractor.py (ステップ1)
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

### glossary_generator.py (ステップ2)
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

### glossary_reviewer.py (ステップ3)
```python
class GlossaryReviewer:
    """用語集の精査を行うクラス"""

    def __init__(self, llm_client: BaseLLMClient):
        self.llm_client = llm_client

    def review(self, glossary: Glossary) -> list[GlossaryIssue]:
        """用語集を精査し、問題点を列挙"""
        ...
```

### glossary_refiner.py (ステップ4)
```python
class GlossaryRefiner:
    """用語集の改善を行うクラス"""

    def __init__(self, llm_client: BaseLLMClient):
        self.llm_client = llm_client

    def refine(self, glossary: Glossary, issues: list[GlossaryIssue], document: Document) -> Glossary:
        """問題点に基づいて用語集を改善"""
        ...
```

## 4. output/ - 出力層

### markdown_writer.py
```python
def write_glossary(glossary: Glossary, output_path: str) -> None:
    """用語集をMarkdown形式で出力"""
    ...
```
