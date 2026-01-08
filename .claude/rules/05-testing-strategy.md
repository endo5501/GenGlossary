# テスト戦略

このドキュメントでは、GenGlossaryプロジェクトのテスト戦略、カバレッジ目標、モック戦略について説明します。

## カバレッジ目標

**目標**: 80%以上

```bash
# カバレッジ測定
$ uv run pytest --cov=genglossary --cov-report=html
```

## テストの種類

### 1. ユニットテスト（最優先）

**対象**: 個々のクラス、メソッドの機能

**例**: `tests/models/test_document.py`

```python
class TestDocument:
    """Test cases for Document model."""

    def test_create_document(self) -> None:
        """Test creating a Document with file_path and content."""
        doc = Document(
            file_path="/path/to/file.txt",
            content="Line 1\nLine 2\nLine 3",
        )
        assert doc.file_path == "/path/to/file.txt"
        assert doc.content == "Line 1\nLine 2\nLine 3"
```

**特徴**:
- ✅ 高速実行
- ✅ 依存関係をモック化
- ✅ TDDサイクルで作成

### 2. 統合テスト（推奨）

**対象**: 複数のコンポーネントの連携

**例**: TermExtractor + OllamaClient

```python
@respx.mock
def test_term_extractor_with_mocked_llm():
    """Test TermExtractor with mocked OllamaClient."""
    # Ollama APIをモック
    respx.post("http://localhost:11434/api/generate").mock(
        return_value=Response(
            200,
            json={"response": '{"terms": ["用語1", "用語2"]}'}
        )
    )

    # 統合テスト
    client = OllamaClient()
    extractor = TermExtractor(client)
    doc = Document(file_path="/test.txt", content="テスト文章")

    terms = extractor.extract(doc)
    assert terms == ["用語1", "用語2"]
```

**特徴**:
- ✅ 実際の連携をテスト
- ✅ 外部依存（Ollama）はモック化
- ✅ エンドツーエンドに近い

### 3. E2Eテスト（オプション）

**対象**: 全パイプラインの動作

**実行条件**: 実際のOllamaサーバーが必要

```python
@pytest.mark.e2e
@pytest.mark.skipif(not is_ollama_running(), reason="Ollama server not running")
def test_full_pipeline_e2e():
    """Test the full glossary generation pipeline."""
    # 実際のOllamaサーバーを使用
    client = OllamaClient()

    # 全パイプラインを実行
    doc = load_document("target_docs/sample.txt")
    terms = TermExtractor(client).extract(doc)
    glossary = GlossaryGenerator(client).generate(terms, doc)
    issues = GlossaryReviewer(client).review(glossary)
    final = GlossaryRefiner(client).refine(glossary, issues, doc)

    # 基本的な検証
    assert len(final.terms) > 0
    assert all(term.definition for term in final.terms)
```

**特徴**:
- ✅ 本番環境に近い
- ❌ 実行が遅い（数分）
- ❌ Ollamaサーバーが必要

## モック戦略

### OllamaClient のモック化

#### パターン1: respx でHTTPモック（推奨）

```python
import respx
from httpx import Response

@respx.mock
def test_ollama_client_generate():
    """Test OllamaClient.generate with mocked HTTP."""
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

**利点**:
- ✅ 実際のHTTPレイヤーをテスト
- ✅ リトライロジックもテスト可能
- ✅ エラーシナリオのテストが容易

#### パターン2: MagicMock （シンプルなテスト向け）

```python
from unittest.mock import MagicMock

def test_term_extractor_with_mock_client():
    """Test TermExtractor with mocked LLM client."""
    mock_client = MagicMock(spec=BaseLLMClient)
    mock_client.generate.return_value = '{"terms": ["用語1", "用語2"]}'

    extractor = TermExtractor(mock_client)
    doc = Document(file_path="/test.txt", content="テスト")

    # テスト実行
    terms = extractor.extract(doc)

    # モックが呼ばれたことを確認
    mock_client.generate.assert_called_once()
    assert "テスト" in mock_client.generate.call_args[0][0]
```

**利点**:
- ✅ シンプル
- ✅ 呼び出し回数の検証が容易
- ❌ HTTPレイヤーはテストしない

### DocumentLoader のモック化

#### pytest の tmp_path フィクスチャ

```python
def test_load_document(tmp_path):
    """Test loading a document from file."""
    # 一時ファイルを作成
    test_file = tmp_path / "test.txt"
    test_file.write_text("Line 1\nLine 2\nLine 3")

    # ドキュメントをロード
    doc = load_document(str(test_file))

    assert doc.file_path == str(test_file)
    assert doc.content == "Line 1\nLine 2\nLine 3"
```

**利点**:
- ✅ 実際のファイルI/Oをテスト
- ✅ 一時ファイルは自動削除
- ✅ ファイルパスの扱いをテスト

## pytestフィクスチャの活用

### 共通フィクスチャの定義

```python
# conftest.py

import pytest
from genglossary.models.document import Document

@pytest.fixture
def sample_document():
    """サンプルドキュメントを返すフィクスチャ."""
    return Document(
        file_path="/test.txt",
        content="Line 1\nLine 2\nLine 3\nLine 4\nLine 5"
    )

@pytest.fixture
def mock_llm_client():
    """モックLLMクライアントを返すフィクスチャ."""
    from unittest.mock import MagicMock
    client = MagicMock(spec=BaseLLMClient)
    return client
```

### フィクスチャの使用

```python
def test_get_context_default(sample_document):
    """Test get_context with sample document."""
    context = sample_document.get_context(3)
    assert context == ["Line 2", "Line 3", "Line 4"]

def test_term_extractor(sample_document, mock_llm_client):
    """Test TermExtractor with fixtures."""
    mock_llm_client.generate.return_value = '{"terms": ["用語1"]}'

    extractor = TermExtractor(mock_llm_client)
    terms = extractor.extract(sample_document)

    assert terms == ["用語1"]
```

## パラメタライズドテスト

複数の入力をテストする場合。

```python
@pytest.mark.parametrize("line_number,context_lines,expected", [
    (3, 1, ["Line 2", "Line 3", "Line 4"]),
    (3, 2, ["Line 1", "Line 2", "Line 3", "Line 4", "Line 5"]),
    (1, 1, ["Line 1", "Line 2"]),
    (5, 1, ["Line 4", "Line 5"]),
])
def test_get_context_parametrized(sample_document, line_number, context_lines, expected):
    """Test get_context with various parameters."""
    context = sample_document.get_context(line_number, context_lines)
    assert context == expected
```

**利点**:
- ✅ 複数のケースを簡潔に記述
- ✅ 各ケースが独立してテスト
- ✅ テストの可読性向上

## エラーケースのテスト

### 例外のテスト

```python
def test_get_line_invalid_index_raises_error():
    """Test get_line with invalid index raises IndexError."""
    doc = Document(file_path="/test.txt", content="Line 1\nLine 2")

    with pytest.raises(IndexError) as exc_info:
        doc.get_line(3)

    assert "out of range" in str(exc_info.value)
```

### ✅ 良い例（具体的なエラーメッセージを検証）

```python
with pytest.raises(IndexError) as exc_info:
    doc.get_line(3)

assert "Line number 3 out of range (1-2)" in str(exc_info.value)
```

### ❌ 悪い例（例外の種類のみ検証）

```python
with pytest.raises(IndexError):
    doc.get_line(3)
# エラーメッセージを検証していない
```

## テスト実行

### 全テスト実行

```bash
$ uv run pytest
```

### 特定のテストファイル

```bash
$ uv run pytest tests/models/test_document.py
```

### 特定のテストケース

```bash
$ uv run pytest tests/models/test_document.py::TestDocument::test_get_context_default
```

### カバレッジ付き

```bash
$ uv run pytest --cov=genglossary --cov-report=html
$ open htmlcov/index.html
```

### E2Eテストをスキップ

```bash
$ uv run pytest -m "not e2e"
```

## 関連ドキュメント

- [TDDワークフロー](@.claude/rules/01-tdd-workflow.md) - テストファースト開発
- [アーキテクチャ](@.claude/rules/03-architecture.md) - テスト対象のモジュール構成
- [モックパターン集](@.claude/rules/examples/mock-patterns.md) - 詳細なモック例
