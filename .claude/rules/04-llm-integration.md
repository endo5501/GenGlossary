# LLM統合パターン

このドキュメントでは、GenGlossaryにおけるOllama統合の設計パターン、理由、ベストプラクティスを説明します。

**参照コード**: `src/genglossary/llm/ollama_client.py`

## なぜこの設計なのか

### 1. リトライロジック
**理由**: Ollamaサーバーは一時的なネットワークエラーやタイムアウトが発生する可能性があるため、リトライで信頼性を向上させます。

### 2. 構造化出力（Pydantic）
**理由**: LLMの出力をPydanticモデルでバリデーションすることで、型安全性を確保し、予期しない形式のデータを早期に検出できます。

### 3. JSON抽出の正規表現フォールバック
**理由**: LLMが余分なテキストを含める場合があるため、正規表現で柔軟に対応します。

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

詳しくは [モックパターン集](@.claude/rules/examples/mock-patterns.md) を参照。

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

## 関連ドキュメント

- [アーキテクチャ](@.claude/rules/03-architecture.md) - LLM層の位置づけ
- [テスト戦略](@.claude/rules/05-testing-strategy.md) - モック戦略
- [モックパターン集](@.claude/rules/examples/mock-patterns.md) - respxの詳細
- [プロンプト例集](@.claude/rules/examples/llm-prompt-examples.md) - 実際のプロンプト
