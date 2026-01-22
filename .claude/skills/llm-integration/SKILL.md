---
name: llm-integration
description: "LLM integration patterns for GenGlossary using Ollama and OpenAI-compatible APIs. Covers retry logic, structured output with Pydantic, JSON extraction, prompt design best practices, and error handling. Use when: (1) Implementing LLM API calls, (2) Designing prompts for term extraction/glossary generation, (3) Handling LLM response parsing, (4) Setting up retry and timeout logic, (5) Mocking LLM calls in tests."
---

# LLM統合パターン

このスキルでは、GenGlossaryにおけるLLM統合（Ollama、OpenAI互換API）の設計パターン、理由、ベストプラクティスを説明します。

**参照コード**:
- `src/genglossary/llm/ollama_client.py` - Ollama専用クライアント
- `src/genglossary/llm/openai_compatible_client.py` - OpenAI互換APIクライアント

## なぜこの設計なのか

### 1. リトライロジック
**理由**: Ollamaサーバーは一時的なネットワークエラーやタイムアウトが発生する可能性があるため、リトライで信頼性を向上させます。

### 2. 構造化出力（Pydantic）
**理由**: LLMの出力をPydanticモデルでバリデーションすることで、型安全性を確保し、予期しない形式のデータを早期に検出できます。

### 3. JSON抽出の正規表現フォールバック
**理由**: LLMが余分なテキストを含める場合があるため、正規表現で柔軟に対応します。

## プロバイダーの選択

GenGlossaryは以下のLLMプロバイダーをサポートします：

| プロバイダー | クライアント | エンドポイント | 特徴 |
|------------|-------------|--------------|------|
| Ollama | `OllamaClient` | `/api/generate` | ローカル実行、プライバシー確保 |
| OpenAI | `OpenAICompatibleClient` | `/v1/chat/completions` | 高品質、API課金 |
| Azure OpenAI | `OpenAICompatibleClient` | `/chat/completions?api-version=...` | エンタープライズ向け |
| llama.cpp | `OpenAICompatibleClient` | `/v1/chat/completions` | ローカル実行、OpenAI互換 |

## Ollama統合の基本

### エンドポイント

```python
# ✅ 良い例
base_url = "http://localhost:11434"
endpoint = f"{base_url}/api/generate"

# ❌ 悪い例
endpoint = "http://localhost:11434/api/generate/"  # 末尾のスラッシュは不要
base_url = "localhost:11434"  # スキーマ（http://）が必要
```

## OpenAI互換API統合の基本

### エンドポイント

OpenAI互換APIは統一されたエンドポイント `/v1/chat/completions` を使用します。

```python
# ✅ 良い例
base_url = "https://api.openai.com/v1"
endpoint = f"{base_url}/chat/completions"

# Azure OpenAIの場合はapi-versionが必要
base_url = "https://your-resource.openai.azure.com"
endpoint = f"{base_url}/chat/completions?api-version=2024-02-15-preview"
```

### 初期化

```python
# ✅ 良い例（デフォルト値を提供）
class OllamaClient(BaseLLMClient):
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "dengcao/Qwen3-30B-A3B-Instruct-2507:latest",
        timeout: float = 30.0,
        max_retries: int = 3
    ):
        self.base_url = base_url.rstrip("/")  # 末尾のスラッシュを削除
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.client = httpx.Client(timeout=timeout)
```

### OpenAI互換APIの初期化

```python
# ✅ 良い例（プロバイダー別の認証を考慮）
class OpenAICompatibleClient(BaseLLMClient):
    def __init__(
        self,
        base_url: str = "https://api.openai.com/v1",
        api_key: str | None = None,
        model: str = "gpt-4o-mini",
        timeout: float = 60.0,
        max_retries: int = 3,
        api_version: str | None = None,  # Azure用
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.api_version = api_version
        self.client = httpx.Client(timeout=timeout)

    @property
    def _headers(self) -> dict[str, str]:
        """Get authentication headers based on provider."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            # Azure uses api-key header
            if "azure" in self.base_url.lower():
                headers["api-key"] = self.api_key
            # OpenAI and others use Bearer token
            else:
                headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
```

**ポイント**:
- ✅ Azureと OpenAIで認証ヘッダーが異なる
- ✅ AzureはURLに `azure` を含むことで自動判定
- ✅ API versionはAzure専用（オプショナル）

## リトライロジックの実装

### 実装例

```python
def _request_with_retry(self, url: str, payload: dict) -> httpx.Response:
    """Execute HTTP request with exponential backoff retry logic.

    Args:
        url: The API endpoint URL.
        payload: The JSON payload to send.

    Returns:
        The HTTP response.

    Raises:
        httpx.HTTPError: If all retries fail.
    """
    last_error = None

    for attempt in range(self.max_retries):
        try:
            response = self.client.post(url, json=payload)
            response.raise_for_status()
            return response

        except httpx.HTTPError as e:
            last_error = e
            if attempt < self.max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                time.sleep(wait_time)

    raise last_error
```

**ポイント**:
- ✅ 指数バックオフ（1秒 → 2秒 → 4秒）
- ✅ 最後のエラーを保持して再スロー
- ✅ 最終試行ではスリープしない

### なぜ指数バックオフなのか

```python
# ✅ 指数バックオフ（推奨）
wait_time = 2 ** attempt  # 1, 2, 4秒

# ❌ 固定ウェイト（サーバー負荷が高い場合に不適切）
wait_time = 1  # 常に1秒

# ❌ ランダムウェイト（予測不可能）
wait_time = random.uniform(1, 5)
```

**理由**:
- サーバーが高負荷の場合、間隔を空けることで回復の時間を与える
- 固定ウェイトは、多数のクライアントが同時にリトライすると「雷の群れ」問題を引き起こす
- 指数バックオフは業界標準（AWS, Google Cloud など）

### OpenAI互換API のリトライ戦略

```python
def _request_with_retry(self, payload: dict) -> httpx.Response:
    """Make HTTP request with provider-specific retry logic."""
    params = {}
    if self.api_version:  # Azure only
        params["api-version"] = self.api_version

    for attempt in range(self.max_retries + 1):
        try:
            response = self.client.post(
                self._endpoint_url,
                json=payload,
                headers=self._headers,
                params=params,
            )

            # Handle rate limiting (429)
            if response.status_code == 429:
                if attempt < self.max_retries:
                    # Check Retry-After header
                    retry_after = int(response.headers.get("Retry-After", 2 ** attempt))
                    time.sleep(min(retry_after, 60))  # Cap at 60 seconds
                    continue

            response.raise_for_status()
            return response

        except httpx.HTTPStatusError as e:
            # Don't retry on client errors (4xx except 429)
            if 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                raise

            # Retry on server errors (5xx)
            if attempt < self.max_retries and e.response.status_code >= 500:
                time.sleep(2 ** attempt)
                continue
            raise
```

**ポイント**:
- ✅ 429（Rate Limit）は `Retry-After` ヘッダーを確認
- ✅ 4xx（401, 400など）は即座にエラー（リトライ不可）
- ✅ 5xxはリトライ可能
- ✅ Azure用の `api-version` クエリパラメータを追加

## 構造化出力のパターン

### 基本パターン

```python
from pydantic import BaseModel

class TermExtractionResult(BaseModel):
    """用語抽出結果のモデル"""
    terms: list[str]

# ✅ 良い例（構造化出力を使用）
result = client.generate_structured(
    prompt="文章から用語を抽出してください: ...",
    response_model=TermExtractionResult
)
terms = result.terms  # 型安全

# ❌ 悪い例（辞書で返す）
result_dict = client.generate_json(prompt="...")
terms = result_dict["terms"]  # KeyError の可能性、型チェック不可
```

### プロンプトの構築

```python
def generate_structured(
    self,
    prompt: str,
    response_model: Type[T],
    max_json_retries: int = 3
) -> T:
    """Generate structured output with JSON schema."""
    # JSON schema を追加
    json_prompt = (
        f"{prompt}\n\n"
        f"Please respond in valid JSON format matching this structure: "
        f"{response_model.model_json_schema()}"
    )

    url = f"{self.base_url}/api/generate"
    payload = {
        "model": self.model,
        "prompt": json_prompt,
        "stream": False
    }

    # HTTPリトライ + JSONパースリトライ
    for attempt in range(max_json_retries):
        response = self._request_with_retry(url, payload)
        response_text = response.json()["response"]

        # JSONパースを試行
        parsed_model = self._parse_json_response(response_text, response_model)
        if parsed_model is not None:
            return parsed_model

        # リトライ前に短い待機
        if attempt < max_json_retries - 1:
            time.sleep(0.5)

    raise ValueError(f"Failed to parse structured output after {max_json_retries} attempts")
```

**ポイント**:
- ✅ JSON schema を明示的に追加
- ✅ HTTPリトライとJSONパースリトライを分離
- ✅ パース失敗時は短い待機後にリトライ

### OpenAI互換API でのJSON mode

OpenAI互換APIは `response_format` で JSON モードをサポートします。

```python
def generate_structured(
    self,
    prompt: str,
    response_model: Type[T],
    max_json_retries: int = 3
) -> T:
    """Generate structured output using JSON mode."""
    json_prompt = f"{prompt}\n\nPlease respond in valid JSON format matching this structure: {response_model.model_json_schema()}"

    payload = {
        "model": self.model,
        "messages": [{"role": "user", "content": json_prompt}],
        "response_format": {"type": "json_object"},  # JSON mode
    }

    for attempt in range(max_json_retries):
        response = self._request_with_retry(payload)
        response_text = response.json()["choices"][0]["message"]["content"]

        parsed_model = self._parse_json_response(response_text, response_model)
        if parsed_model is not None:
            return parsed_model

        if attempt < max_json_retries - 1:
            time.sleep(0.5)

    raise ValueError(f"Failed to parse structured output after {max_json_retries} attempts")
```

**ポイント**:
- ✅ `response_format: {"type": "json_object"}` でJSON出力を強制
- ✅ Ollamaと異なり、メッセージ形式（`messages`）を使用
- ✅ レスポンスは `choices[0].message.content` から取得

## JSON抽出の正規表現パターン

LLMが余分なテキストを含める場合の対処法。

### 実装例

```python
def _parse_json_response(self, text: str, response_model: Type[T]) -> T | None:
    """Parse JSON from LLM response with fallback strategies.

    Args:
        text: The raw response text from LLM.
        response_model: Pydantic model for validation.

    Returns:
        Validated model instance, or None if parsing fails.
    """
    # パターン1: 直接JSONパース
    try:
        data = json.loads(text)
        return response_model.model_validate(data)
    except (json.JSONDecodeError, ValidationError):
        pass

    # パターン2: コードブロック内のJSONを抽出
    match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(1))
            return response_model.model_validate(data)
        except (json.JSONDecodeError, ValidationError):
            pass

    # パターン3: 最初のJSONオブジェクトを抽出
    match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text)
    if match:
        try:
            data = json.loads(match.group())
            return response_model.model_validate(data)
        except (json.JSONDecodeError, ValidationError):
            pass

    return None
```

**フォールバック戦略**:
1. まずテキスト全体をJSONパース
2. 失敗したら ` ```json ... ``` ` ブロックを抽出
3. それも失敗したら正規表現で最初の `{...}` を抽出

## プロンプト設計のベストプラクティス

### ✅ 良いプロンプト

```python
prompt = f"""
以下の文章から専門用語を抽出してください。

# 抽出基準
- 文章内で2回以上出現する名詞
- 固有名詞、専門用語を優先
- 一般的な単語（「これ」「それ」など）は除外

# 入力文章
{document.content}

# 出力形式
JSON形式で以下の構造で返してください:
{{"terms": ["用語1", "用語2", "用語3"]}}
"""
```

**良い点**:
- ✅ タスクを明確に定義
- ✅ 具体的な基準を示す
- ✅ 期待する出力形式を明示
- ✅ JSON schemaの例を提供

### ❌ 悪いプロンプト

```python
# 曖昧で形式不明
prompt = "用語を抽出してください"

# 出力形式が不明確
prompt = "文章から用語を抽出して、リストで返してください"

# 基準が不明確
prompt = "重要な単語を見つけてください"
```

### プロンプトテンプレートのパターン

```python
# ✅ テンプレート化（推奨）
TERM_EXTRACTION_PROMPT = """
以下の文章から専門用語を抽出してください。

# 抽出基準
{criteria}

# 入力文章
{content}

# 出力形式
JSON形式: {{"terms": ["用語1", "用語2"]}}
"""

prompt = TERM_EXTRACTION_PROMPT.format(
    criteria="文章内で2回以上出現する名詞",
    content=document.content
)

# ❌ ハードコード（保守性が低い）
prompt = f"以下の文章から...{document.content}..."
```

## エラーハンドリング

### ✅ 良い例（具体的な例外）

```python
try:
    result = client.generate_structured(prompt, TermExtractionResult)
except httpx.HTTPError as e:
    logger.error(f"Ollama API request failed: {e}")
    raise
except ValueError as e:
    logger.error(f"Response parsing failed: {e}")
    # JSONパースのフォールバックを試行済み
    raise
except ValidationError as e:
    logger.error(f"Response validation failed: {e.errors()}")
    raise
```

### ❌ 悪い例（全例外を握りつぶす）

```python
try:
    result = client.generate_structured(prompt, TermExtractionResult)
except Exception:
    pass  # エラーを無視 → デバッグ不可能
    return []  # デフォルト値を返す → 問題を隠蔽
```

## テストでのモック化

### respx を使用したHTTPモック

```python
import respx
from httpx import Response

@respx.mock
def test_generate_returns_response_text():
    """Test generate method returns response text."""
    # Ollama APIのレスポンスをモック
    respx.post("http://localhost:11434/api/generate").mock(
        return_value=Response(
            200,
            json={"response": "Generated text"}
        )
    )

    client = OllamaClient()
    result = client.generate("Test prompt")

    assert result == "Generated text"
```

**ポイント**:
- ✅ 実際のHTTPリクエストをインターセプト
- ✅ モックレスポンスをJSON形式で定義
- ✅ ネットワークなしでテスト可能

## パフォーマンス最適化

### タイムアウト設定

```python
# ✅ 適切なタイムアウト
client = OllamaClient(timeout=30.0)  # 30秒

# ❌ タイムアウトなし（ハング の可能性）
client = httpx.Client()  # デフォルトはタイムアウトなし
```

### ストリーミングの無効化

```python
payload = {
    "model": self.model,
    "prompt": prompt,
    "stream": False  # 必ずFalseに設定
}
```

**理由**: ストリーミングは複雑で、エラーハンドリングが困難。バッチ処理で十分。

## プロバイダー別の実装例

### プロバイダー選択のファクトリパターン

```python
from genglossary.llm.base import BaseLLMClient
from genglossary.llm.ollama_client import OllamaClient
from genglossary.llm.openai_compatible_client import OpenAICompatibleClient
from genglossary.config import Config

def create_llm_client(provider: str, model: str | None = None) -> BaseLLMClient:
    """Create LLM client based on provider.

    Args:
        provider: "ollama" or "openai"
        model: Optional model name

    Returns:
        Configured LLM client
    """
    if provider == "ollama":
        return OllamaClient(
            model=model or "dengcao/Qwen3-30B-A3B-Instruct-2507:latest",
            timeout=180.0,
        )
    elif provider == "openai":
        config = Config()
        return OpenAICompatibleClient(
            base_url=config.openai_base_url,
            api_key=config.openai_api_key,
            model=model or config.openai_model,
            timeout=180.0,
            api_version=config.azure_openai_api_version,
        )
    else:
        raise ValueError(f"Unknown provider: {provider}")
```

**使用例**:

```python
# Ollamaを使用
client = create_llm_client("ollama")

# OpenAI APIを使用
client = create_llm_client("openai", model="gpt-4o-mini")

# Azure OpenAIを使用（環境変数で設定）
# OPENAI_BASE_URL=https://your-resource.openai.azure.com
# AZURE_OPENAI_API_VERSION=2024-02-15-preview
client = create_llm_client("openai")
```

## テストでのプロバイダー別モック

### OpenAI互換APIのモック

```python
import respx
from httpx import Response

@respx.mock
def test_openai_generate_returns_response_text():
    """Test OpenAI-compatible API generate method."""
    # OpenAI APIのレスポンスをモック
    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=Response(
            200,
            json={
                "id": "chatcmpl-123",
                "choices": [{
                    "message": {"content": "Generated text"}
                }]
            }
        )
    )

    client = OpenAICompatibleClient(
        base_url="https://api.openai.com/v1",
        api_key="test-key"
    )
    result = client.generate("Test prompt")

    assert result == "Generated text"
```

**ポイント**:
- ✅ OpenAI APIのレスポンス構造（`choices[].message.content`）に従う
- ✅ Ollamaとは異なるエンドポイント（`/v1/chat/completions`）

## 関連ドキュメント

- [プロンプト例集](references/prompt-examples.md) - 4ステップごとの実際のプロンプト設計例
- `docs/architecture.md` - LLM層の位置づけ
