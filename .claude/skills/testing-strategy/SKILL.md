---
name: testing-strategy
description: Testing strategy and techniques for Python projects using pytest. Covers test types (unit, integration, E2E), mocking strategies (respx, MagicMock), fixtures, parametrized tests, and test execution. Use when writing tests, setting up mocks, or deciding testing approach.
---

# Testing Strategy

## Coverage Goal

**Target**: 80%+

```bash
uv run pytest --cov=genglossary --cov-report=html
```

## Test Types

### 1. Unit Tests (Priority)

Test individual classes/methods in isolation.

```python
def test_create_document():
    """Test creating a Document."""
    doc = Document(file_path="/test.txt", content="Line 1\nLine 2")
    assert doc.file_path == "/test.txt"
    assert doc.content == "Line 1\nLine 2"
```

**Characteristics:**
- ✅ Fast execution
- ✅ Mock external dependencies
- ✅ Created with TDD cycle

### 2. Integration Tests (Recommended)

Test multiple components working together.

```python
@respx.mock
def test_term_extractor_with_mocked_llm():
    """Test TermExtractor with mocked OllamaClient."""
    respx.post("http://localhost:11434/api/generate").mock(
        return_value=Response(200, json={"response": '{"terms": ["用語1"]}'})
    )

    extractor = TermExtractor(OllamaClient())
    terms = extractor.extract(doc)
    assert terms == ["用語1"]
```

### 3. E2E Tests (Optional)

Test full pipeline. Requires actual Ollama server.

```python
@pytest.mark.e2e
@pytest.mark.skipif(not is_ollama_running(), reason="Ollama not running")
def test_full_pipeline_e2e():
    """Test complete glossary generation."""
    client = OllamaClient()
    doc = load_document("target_docs/sample.txt")
    # ... full pipeline
    assert len(final.terms) > 0
```

## Mocking Strategy

### When to Use Each Approach

**respx (HTTP mocking)**
- Testing HTTP layer
- Testing retry logic
- Testing OllamaClient itself

```python
@respx.mock
def test_ollama_client():
    respx.post("http://localhost:11434/api/generate").mock(
        return_value=Response(200, json={"response": "text"})
    )
    result = client.generate("prompt")
    assert result == "text"
```

**MagicMock (Simple mocking)**
- Testing business logic
- Testing classes that depend on LLM client
- Verifying call counts/arguments

```python
mock_client = MagicMock(spec=BaseLLMClient)
mock_client.generate.return_value = '{"terms": []}'
extractor = TermExtractor(mock_client)
extractor.extract(doc)
mock_client.generate.assert_called_once()
```

**tmp_path (File I/O)**
- Testing file operations
- Temporary files auto-deleted after test

```python
def test_load_document(tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    doc = load_document(str(test_file))
    assert doc.content == "content"
```

For detailed mock patterns, see [references/mock-patterns.md](references/mock-patterns.md).

## pytest Fixtures

### Common Fixtures

```python
# conftest.py
@pytest.fixture
def sample_document():
    """Sample document fixture."""
    return Document(file_path="/test.txt", content="Line 1\nLine 2\nLine 3")

@pytest.fixture
def mock_llm_client():
    """Mock LLM client fixture."""
    client = MagicMock(spec=BaseLLMClient)
    client.generate.return_value = '{"terms": []}'
    return client
```

### Using Fixtures

```python
def test_with_fixtures(sample_document, mock_llm_client):
    extractor = TermExtractor(mock_llm_client)
    terms = extractor.extract(sample_document)
    assert isinstance(terms, list)
```

## Parametrized Tests

Test multiple inputs efficiently.

```python
@pytest.mark.parametrize("line_number,context_lines,expected", [
    (3, 1, ["Line 2", "Line 3", "Line 4"]),
    (1, 1, ["Line 1", "Line 2"]),
    (5, 1, ["Line 4", "Line 5"]),
])
def test_get_context(sample_document, line_number, context_lines, expected):
    context = sample_document.get_context(line_number, context_lines)
    assert context == expected
```

## Error Testing

### Test Exceptions

```python
def test_invalid_index_raises_error():
    doc = Document(file_path="/test.txt", content="Line 1\nLine 2")

    with pytest.raises(IndexError) as exc_info:
        doc.get_line(3)

    assert "out of range" in str(exc_info.value)
```

**✅ Good**: Verify error message
**❌ Bad**: Only verify exception type

## Test Execution

```bash
# All tests
uv run pytest

# Specific file
uv run pytest tests/models/test_document.py

# Specific test
uv run pytest tests/models/test_document.py::test_create_document

# With coverage
uv run pytest --cov=genglossary --cov-report=html
open htmlcov/index.html

# Skip E2E tests
uv run pytest -m "not e2e"
```

## Test File Structure

```
src/genglossary/models/document.py
→ tests/models/test_document.py

src/genglossary/llm/ollama_client.py
→ tests/llm/test_ollama_client.py
```

Rule: Mirror `src/genglossary/` structure in `tests/` with `test_` prefix.
