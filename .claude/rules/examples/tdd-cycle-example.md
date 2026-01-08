# TDDサイクルの完全な例

このドキュメントでは、実際の `Document.get_context()` メソッドの実装を例に、TDDサイクル全体を詳しく解説します。

**参照コード**:
- 実装: `src/genglossary/models/document.py:47-67`
- テスト: `tests/models/test_document.py:75-130`

## シナリオ: Document.get_context()メソッドの追加

### 要件

指定した行番号とその前後N行を取得するメソッドを実装します。

**メソッドシグネチャ**:
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
```

## Phase 1: Red（テスト作成→失敗確認）

### ステップ1-1: テストを作成

```python
# tests/models/test_document.py

def test_get_context_default(self) -> None:
    """Test get_context with default context_lines (1 line before/after)."""
    doc = Document(
        file_path="/path/to/file.txt",
        content="Line 1\nLine 2\nLine 3\nLine 4\nLine 5",
    )
    context = doc.get_context(3)
    assert context == ["Line 2", "Line 3", "Line 4"]

def test_get_context_custom_lines(self) -> None:
    """Test get_context with custom context_lines."""
    doc = Document(
        file_path="/path/to/file.txt",
        content="Line 1\nLine 2\nLine 3\nLine 4\nLine 5",
    )
    context = doc.get_context(3, context_lines=2)
    assert context == ["Line 1", "Line 2", "Line 3", "Line 4", "Line 5"]

def test_get_context_at_start(self) -> None:
    """Test get_context at the start of document."""
    doc = Document(
        file_path="/path/to/file.txt",
        content="Line 1\nLine 2\nLine 3\nLine 4\nLine 5",
    )
    context = doc.get_context(1)
    assert context == ["Line 1", "Line 2"]

def test_get_context_at_end(self) -> None:
    """Test get_context at the end of document."""
    doc = Document(
        file_path="/path/to/file.txt",
        content="Line 1\nLine 2\nLine 3\nLine 4\nLine 5",
    )
    context = doc.get_context(5)
    assert context == ["Line 4", "Line 5"]

def test_get_context_invalid_line_number(self) -> None:
    """Test get_context with invalid line number raises error."""
    doc = Document(
        file_path="/path/to/file.txt",
        content="Line 1\nLine 2",
    )
    with pytest.raises(IndexError):
        doc.get_context(0)
    with pytest.raises(IndexError):
        doc.get_context(3)

def test_get_context_zero_context_lines(self) -> None:
    """Test get_context with zero context_lines returns just the line."""
    doc = Document(
        file_path="/path/to/file.txt",
        content="Line 1\nLine 2\nLine 3",
    )
    context = doc.get_context(2, context_lines=0)
    assert context == ["Line 2"]
```

**ポイント**:
- ✅ 境界条件をテスト（開始位置、終了位置）
- ✅ 正常系と異常系の両方をカバー
- ✅ デフォルト引数とカスタム引数の両方をテスト
- ✅ 各テストが独立して実行可能
- ✅ docstringで何をテストするか明記

### ステップ1-2: テストを実行（失敗を確認）

```bash
$ uv run pytest tests/models/test_document.py::TestDocument::test_get_context_default -v

tests/models/test_document.py::TestDocument::test_get_context_default FAILED [100%]

E   AttributeError: 'Document' object has no attribute 'get_context'

====== 1 failed in 0.15s ======
```

**重要**:
- ❌ `AttributeError` が発生 → 期待通り！
- メソッドがまだ実装されていないことを確認
- もし成功してしまったら、テストが間違っているか既に実装されている

### ステップ1-3: 全テストを実行（新しいテストが失敗することを確認）

```bash
$ uv run pytest tests/models/test_document.py -v

tests/models/test_document.py::TestDocument::test_create_document PASSED
tests/models/test_document.py::TestDocument::test_lines_property PASSED
tests/models/test_document.py::TestDocument::test_get_line_valid_index PASSED
tests/models/test_document.py::TestDocument::test_get_context_default FAILED
tests/models/test_document.py::TestDocument::test_get_context_custom_lines FAILED
tests/models/test_document.py::TestDocument::test_get_context_at_start FAILED
tests/models/test_document.py::TestDocument::test_get_context_at_end FAILED
tests/models/test_document.py::TestDocument::test_get_context_invalid_line_number FAILED
tests/models/test_document.py::TestDocument::test_get_context_zero_context_lines FAILED

====== 6 failed, 3 passed in 0.23s ======
```

**確認事項**:
- ✅ 既存のテスト（3個）はすべてパス
- ✅ 新しいテスト（6個）はすべて失敗
- ✅ 失敗理由は `AttributeError: 'Document' object has no attribute 'get_context'`

### ステップ1-4: テストのみをコミット

```bash
$ git add tests/models/test_document.py
$ git commit -m "Add Document.get_context() tests

Test cases:
- Default context (1 line before/after)
- Custom context lines
- Boundary handling (start and end of document)
- Invalid line number raises IndexError
- Zero context lines returns single line"
```

**コミットのポイント**:
- ✅ テストファイルのみを追加
- ✅ "Add ... tests" という形式
- ✅ 追加したテストケースを箇条書きで説明
- ✅ 実装コードは含めない

## Phase 2: Green（実装→テスト成功）

### ステップ2-1: 最小限の実装

```python
# src/genglossary/models/document.py

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
    # 1. バリデーション
    if line_number < 1 or line_number > self.line_count:
        raise IndexError(
            f"Line number {line_number} out of range (1-{self.line_count})"
        )

    # 2. コンテキスト範囲を計算
    start = max(0, line_number - 1 - context_lines)
    end = min(self.line_count, line_number + context_lines)

    # 3. 指定範囲の行を返す
    return self.lines[start:end]
```

**実装のポイント**:
- ✅ 最小限の実装（YAGNIを守る）
- ✅ バリデーション、計算、返却の3ステップ
- ✅ ドキュメントストリング（docstring）を追加
- ✅ `max()` と `min()` で境界を安全に処理

### ステップ2-2: テストを実行（成功を確認）

```bash
$ uv run pytest tests/models/test_document.py::TestDocument::test_get_context_default -v

tests/models/test_document.py::TestDocument::test_get_context_default PASSED [100%]

====== 1 passed in 0.05s ======
```

### ステップ2-3: 全テストを実行

```bash
$ uv run pytest tests/models/test_document.py -v

tests/models/test_document.py::TestDocument::test_create_document PASSED
tests/models/test_document.py::TestDocument::test_lines_property PASSED
tests/models/test_document.py::TestDocument::test_get_line_valid_index PASSED
tests/models/test_document.py::TestDocument::test_get_context_default PASSED
tests/models/test_document.py::TestDocument::test_get_context_custom_lines PASSED
tests/models/test_document.py::TestDocument::test_get_context_at_start PASSED
tests/models/test_document.py::TestDocument::test_get_context_at_end PASSED
tests/models/test_document.py::TestDocument::test_get_context_invalid_line_number PASSED
tests/models/test_document.py::TestDocument::test_get_context_zero_context_lines PASSED

====== 9 passed in 0.18s ======
```

**確認事項**:
- ✅ 新しいテスト（6個）がすべてパス！
- ✅ 既存のテスト（3個）も引き続きパス
- ✅ リグレッションなし

### ステップ2-4: 実装をコミット

```bash
$ git add src/genglossary/models/document.py
$ git commit -m "Implement Document.get_context()

Returns the target line with surrounding context lines,
handling document boundaries correctly using max/min."
```

**コミットのポイント**:
- ✅ 実装ファイルのみを追加
- ✅ "Implement ..." という形式
- ✅ 実装の概要を簡潔に説明
- ✅ 境界処理の方法を明記（max/min）

## Phase 3: Refactor（必要に応じて）

この実装では、すでに簡潔で読みやすいコードなので、リファクタリングは不要です。

もしリファクタリングが必要な場合:

```bash
# リファクタリング後、テストがパスすることを確認
$ uv run pytest tests/models/test_document.py -v
====== 9 passed in 0.18s ======

# コミット
$ git commit -m "Refactor Document.get_context() to improve readability"
```

## 完了確認

### コミット履歴

```bash
$ git log --oneline -2

b3c4d5e Implement Document.get_context()
a2b3c4d Add Document.get_context() tests
```

**理想的なコミット履歴**:
- ✅ 2つのコミット（テスト、実装）
- ✅ 明確なコミットメッセージ
- ✅ テストが先、実装が後

### 全体テストの確認

```bash
$ uv run pytest
====== 15 passed in 1.23s ======
```

✅ すべてのテストがパス！

## ポイントまとめ

### ✅ 良かった点

1. **境界条件のテスト**: 開始位置、終了位置、範囲外のケースをカバー
2. **テストの独立性**: 各テストが独立して実行可能
3. **最小限の実装**: YAGNIを守り、必要最小限のコードで実装
4. **明確なコミット**: テストと実装を分離、メッセージが具体的
5. **リグレッション確認**: 既存のテストも引き続きパス

### ❌ 避けるべきこと

1. テストと実装を同時にコミット
2. テストの失敗を確認せずに実装に進む
3. 過剰な実装（必要ない機能まで追加）
4. 曖昧なコミットメッセージ
5. 境界条件のテスト不足

## 実践での活用

このTDDサイクルを他のメソッドや機能にも適用してください:

1. **TermExtractor.extract()**: 用語抽出ロジック
2. **GlossaryGenerator.generate()**: 用語集生成ロジック
3. **OllamaClient.generate_structured()**: 構造化出力ロジック

**テンプレート**:
```bash
# 1. テストを書く
$ git add tests/<module>/test_<name>.py
$ git commit -m "Add <ClassName>.<method_name>() tests"

# 2. テストを実行（失敗確認）
$ uv run pytest tests/<module>/test_<name>.py -v
# → FAILED

# 3. 実装する
$ git add src/genglossary/<module>/<name>.py
$ git commit -m "Implement <ClassName>.<method_name>()"

# 4. テストを実行（成功確認）
$ uv run pytest tests/<module>/test_<name>.py -v
# → PASSED
```

## 関連ドキュメント

- [TDDワークフロー](@.claude/rules/01-tdd-workflow.md) - TDDの基本ルール
- [Gitワークフロー](@.claude/rules/02-git-workflow.md) - コミット規約
- [良い/悪いコミット例](@.claude/rules/examples/good-bad-commits.md) - コミットメッセージの例
