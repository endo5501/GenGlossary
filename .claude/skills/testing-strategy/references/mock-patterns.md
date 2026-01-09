# モックパターン集

このドキュメントでは、GenGlossaryプロジェクトでよく使うモックパターンを実例とともに紹介します。

## respx を使ったHTTPモック

### パターン1: 基本的なモック

```python
import respx
from httpx import Response

@respx.mock
def test_ollama_client_generate():
    """Test OllamaClient.generate with mocked HTTP."""
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
- ✅ `@respx.mock` デコレータで全HTTPリクエストをインターセプト
- ✅ エンドポイントURLを正確に指定
- ✅ `Response` オブジェクトで実際のレスポンスを模倣

### パターン2: JSONレスポンスのモック

```python
@respx.mock
def test_generate_structured_success():
    """Test generate_structured with valid JSON response."""
    # JSONレスポンスをモック
    respx.post("http://localhost:11434/api/generate").mock(
        return_value=Response(
            200,
            json={"response": '{"terms": ["用語1", "用語2", "用語3"]}'}
        )
    )

    class TermExtractionResult(BaseModel):
        terms: list[str]

    client = OllamaClient()
    result = client.generate_structured(
        prompt="Extract terms",
        response_model=TermExtractionResult
    )

    assert result.terms == ["用語1", "用語2", "用語3"]
```

### パターン3: エラーレスポンスのモック

```python
import pytest

@respx.mock
def test_generate_handles_http_error():
    """Test generate handles HTTP errors with retry."""
    # HTTPエラーをモック
    respx.post("http://localhost:11434/api/generate").mock(
        side_effect=httpx.HTTPError("Connection failed")
    )

    client = OllamaClient(max_retries=1)

    with pytest.raises(httpx.HTTPError):
        client.generate("Test prompt")
```

**ポイント**:
- ✅ `side_effect` で例外をスロー
- ✅ リトライロジックもテスト可能

### パターン4: リトライのテスト

```python
@respx.mock
def test_request_with_retry_succeeds_on_second_attempt():
    """Test retry succeeds on second attempt."""
    # 1回目: 失敗、2回目: 成功
    mock_route = respx.post("http://localhost:11434/api/generate").mock(
        side_effect=[
            httpx.HTTPError("First attempt fails"),
            Response(200, json={"response": "Success on second attempt"})
        ]
    )

    client = OllamaClient(max_retries=3)
    result = client.generate("Test prompt")

    assert result == "Success on second attempt"
    assert mock_route.call_count == 2  # 2回呼ばれたことを確認
```

**ポイント**:
- ✅ `side_effect` のリストで複数のレスポンスを定義
- ✅ `call_count` でリトライ回数を検証

### パターン5: リクエスト内容の検証

```python
@respx.mock
def test_generate_sends_correct_payload():
    """Test generate sends correct payload to Ollama API."""
    mock_route = respx.post("http://localhost:11434/api/generate").mock(
        return_value=Response(200, json={"response": "OK"})
    )

    client = OllamaClient(model="llama2")
    client.generate("Test prompt")

    # リクエストの内容を検証
    assert mock_route.called
    request = mock_route.calls.last.request
    payload = json.loads(request.content)

    assert payload["model"] == "llama2"
    assert payload["prompt"] == "Test prompt"
    assert payload["stream"] is False
```

**ポイント**:
- ✅ `mock_route.calls.last.request` で実際のリクエストを取得
- ✅ ペイロードの中身を詳細に検証

## MagicMock を使ったシンプルなモック

### パターン6: LLMクライアントのモック

```python
from unittest.mock import MagicMock

def test_term_extractor_with_mock_client():
    """Test TermExtractor with mocked LLM client."""
    # モッククライアントを作成
    mock_client = MagicMock(spec=BaseLLMClient)
    mock_client.generate.return_value = '{"terms": ["用語1", "用語2"]}'

    # テスト対象を作成
    extractor = TermExtractor(mock_client)
    doc = Document(file_path="/test.txt", content="テスト文章")

    # 実行
    terms = extractor.extract(doc)

    # 検証
    assert terms == ["用語1", "用語2"]
    mock_client.generate.assert_called_once()
```

**ポイント**:
- ✅ `MagicMock(spec=BaseLLMClient)` で型をチェック
- ✅ `return_value` で戻り値を設定
- ✅ `assert_called_once()` で呼び出しを検証

### パターン7: 呼び出し引数の検証

```python
def test_term_extractor_sends_correct_prompt():
    """Test TermExtractor sends correct prompt to LLM."""
    mock_client = MagicMock(spec=BaseLLMClient)
    mock_client.generate.return_value = '{"terms": []}'

    extractor = TermExtractor(mock_client)
    doc = Document(file_path="/test.txt", content="量子コンピュータ")

    extractor.extract(doc)

    # 呼び出し引数を取得
    call_args = mock_client.generate.call_args
    prompt = call_args[0][0]  # 最初の位置引数

    # プロンプトに必要な要素が含まれていることを確認
    assert "量子コンピュータ" in prompt
    assert "JSON" in prompt
```

**ポイント**:
- ✅ `call_args` で実際の引数を取得
- ✅ プロンプトの内容を検証

### パターン8: 複数回の呼び出し

```python
def test_glossary_generator_calls_llm_for_each_term():
    """Test GlossaryGenerator calls LLM for each term."""
    mock_client = MagicMock(spec=BaseLLMClient)
    mock_client.generate_structured.return_value = Term(
        text="用語",
        definition="定義",
        occurrences=[]
    )

    generator = GlossaryGenerator(mock_client)
    terms = ["用語1", "用語2", "用語3"]
    doc = Document(file_path="/test.txt", content="...")

    glossary = generator.generate(terms, doc)

    # 3回呼ばれたことを確認
    assert mock_client.generate_structured.call_count == 3
```

## pytestフィクスチャとモックの組み合わせ

### パターン9: フィクスチャでモックを提供

```python
# conftest.py

import pytest
from unittest.mock import MagicMock

@pytest.fixture
def mock_llm_client():
    """モックLLMクライアントを返すフィクスチャ."""
    client = MagicMock(spec=BaseLLMClient)
    client.generate.return_value = '{"terms": []}'
    return client

@pytest.fixture
def sample_document():
    """サンプルドキュメントを返すフィクスチャ."""
    return Document(
        file_path="/test.txt",
        content="Line 1\nLine 2\nLine 3"
    )
```

```python
# test_term_extractor.py

def test_extract_with_fixtures(mock_llm_client, sample_document):
    """Test term extraction with fixtures."""
    extractor = TermExtractor(mock_llm_client)
    terms = extractor.extract(sample_document)

    assert isinstance(terms, list)
    mock_llm_client.generate.assert_called_once()
```

## 一時ファイルのモック（tmp_path）

### パターン10: ファイルI/Oのテスト

```python
def test_load_document(tmp_path):
    """Test loading a document from file."""
    # 一時ファイルを作成
    test_file = tmp_path / "sample.txt"
    test_file.write_text("Line 1\nLine 2\nLine 3", encoding="utf-8")

    # ドキュメントをロード
    doc = load_document(str(test_file))

    assert doc.file_path == str(test_file)
    assert doc.content == "Line 1\nLine 2\nLine 3"
    assert doc.line_count == 3
```

**ポイント**:
- ✅ `tmp_path` フィクスチャで一時ディレクトリを取得
- ✅ テスト終了後に自動削除される
- ✅ 実際のファイルI/Oをテスト

### パターン11: Markdown出力のテスト

```python
def test_write_glossary(tmp_path):
    """Test writing glossary to Markdown file."""
    glossary = Glossary(
        terms=[
            Term(text="用語1", definition="定義1", occurrences=[]),
            Term(text="用語2", definition="定義2", occurrences=[])
        ]
    )

    output_file = tmp_path / "glossary.md"
    write_glossary(glossary, str(output_file))

    # ファイルが作成されたことを確認
    assert output_file.exists()

    # 内容を検証
    content = output_file.read_text(encoding="utf-8")
    assert "用語1" in content
    assert "定義1" in content
    assert "用語2" in content
```

## モック戦略のまとめ

### いつrespxを使うか

- ✅ HTTPレイヤーをテストしたい
- ✅ リトライロジックをテストしたい
- ✅ 実際のHTTPエラーハンドリングをテストしたい
- ✅ OllamaClient 自体をテストする場合

### いつMagicMockを使うか

- ✅ シンプルなユニットテスト
- ✅ ビジネスロジックに集中したい
- ✅ LLMクライアントに依存するクラスをテストする場合
- ✅ 呼び出し回数や引数を検証したい

### いつtmp_pathを使うか

- ✅ ファイルI/Oをテストしたい
- ✅ 実際のファイルシステムの挙動をテストしたい
- ✅ テスト後のクリーンアップが必要

## よくある間違い

### ❌ 実際のHTTPリクエストを送る

```python
# ❌ 悪い例（実際のOllamaサーバーが必要）
def test_ollama_client():
    client = OllamaClient()
    result = client.generate("Test")  # 実際のHTTPリクエスト
    assert result
```

**問題点**:
- Ollamaサーバーが起動していないとテストが失敗
- テストが遅い
- ネットワークに依存

### ❌ モックの設定ミス

```python
# ❌ 悪い例（side_effectの使い方が間違っている）
@respx.mock
def test_retry():
    respx.post("http://localhost:11434/api/generate").mock(
        side_effect=Response(200, json={"response": "OK"})
    )
    # side_effectには例外かリストを渡すべき
```

### ❌ 呼び出し検証の不足

```python
# ❌ 悪い例（モックが実際に呼ばれたか検証していない）
def test_term_extractor(mock_llm_client):
    mock_llm_client.generate.return_value = '{"terms": []}'
    extractor = TermExtractor(mock_llm_client)
    extractor.extract(doc)
    # assert_called_once() がない
```

## 関連ドキュメント

- テスト戦略 → `/testing-strategy` スキルを使用
- TDDワークフロー → `/tdd-workflow` スキルを使用
- LLM統合 → `/llm-integration` スキルを使用
