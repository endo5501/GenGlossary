# TDDワークフロー

## 優先度: 必須（MUST）

**このプロジェクトはテスト駆動開発（TDD）を厳守します。**

## なぜTDDなのか

### 1. 品質担保
テストが要件の明確化と正しさの証明になります。実装前にテストを書くことで、何を作るべきかが明確になります。

### 2. リグレッション防止
変更時の影響を即座に検知できます。新しい機能を追加したり、リファクタリングを行ったりする際も、既存のテストが破壊されていないことを確認できます。

### 3. 設計改善
テスト可能性を考慮した設計になります。テストしやすいコードは、疎結合で責務が明確なコードです。

### 4. ドキュメント
テストが動作仕様書として機能します。コードの使い方や期待される動作がテストから読み取れます。

## TDDサイクル（Red-Green-Commit）

### ステップ1: Red（テスト作成→失敗確認）

#### 1-1. テストファイルを作成

```python
# tests/models/test_document.py

def test_create_document_with_valid_path():
    """Test creating a document with a valid file path."""
    doc = Document(file_path="/path/to/file.txt", content="Hello World")
    assert doc.file_path == "/path/to/file.txt"
    assert doc.content == "Hello World"
```

#### 1-2. テストを実行（失敗を確認）

```bash
$ uv run pytest tests/models/test_document.py -v

FAILED - ImportError: cannot import name 'Document' from 'genglossary.models'
```

**重要**: 必ず失敗を確認してください。失敗しないテストは、テストが正しく書けていないか、既に実装されているかのどちらかです。

#### 1-3. テストのみをコミット

```bash
$ git add tests/models/test_document.py
$ git commit -m "Add Document model tests

Test cases:
- Create document with valid file path
- Verify file_path and content attributes"
```

**✅ 良い例**:
- テストが明確な期待値を定義している
- 失敗を確認してからコミット
- コミットメッセージが「Add ... tests」という形式
- 複数のテストケースがある場合は箇条書きで説明

**❌ 悪い例**:
```bash
# ❌ テストと実装を同時にコミット
$ git add tests/ src/
$ git commit -m "Add Document model"

# ❌ テスト実行せずにコミット
$ git add tests/
$ git commit -m "add tests"  # 小文字始まり、曖昧

# ❌ 失敗を確認していない
# → テストが既存のコードをテストしているだけかもしれない
```

### ステップ2: Green（実装→テスト成功）

#### 2-1. 実装コードを作成

```python
# src/genglossary/models/document.py

from pydantic import BaseModel

class Document(BaseModel):
    """A document with file path and content."""

    file_path: str
    content: str
```

**最小限の実装**: テストをパスする最小限のコードを書きます（YAGNI: You Aren't Gonna Need It）。

#### 2-2. テストを実行（成功を確認）

```bash
$ uv run pytest tests/models/test_document.py -v

tests/models/test_document.py::test_create_document_with_valid_path PASSED [100%]

====== 1 passed in 0.05s ======
```

#### 2-3. 実装をコミット

```bash
$ git add src/genglossary/models/document.py
$ git commit -m "Implement Document model

Pydantic BaseModel with file_path and content attributes."
```

**✅ 良い例**:
- すべてのテストがパス
- 最小限の実装（過剰な機能を追加しない）
- コミットメッセージが「Implement ...」という形式
- 実装の概要を簡潔に説明

**❌ 悪い例**:
```bash
# ❌ テストがまだ失敗しているのにコミット
$ uv run pytest  # FAILED
$ git commit -m "Implement Document model"  # NG!

# ❌ 過剰な実装
class Document(BaseModel):
    file_path: str
    content: str
    metadata: dict  # テストで要求されていない
    created_at: datetime  # YAGNI!

# ❌ 曖昧なコミットメッセージ
$ git commit -m "update code"
$ git commit -m "fix"
```

### ステップ3: Refactor（必要に応じて）

コードの品質を改善します。リファクタリング後も全テストがパスすることを確認してコミット。

```bash
$ uv run pytest  # すべてパス
$ git commit -m "Refactor Document model to use field validators"
```

## 実践ガイド

### テストファイルの配置ルール

```
src/genglossary/models/document.py
→ tests/models/test_document.py

src/genglossary/llm/ollama_client.py
→ tests/llm/test_ollama_client.py

src/genglossary/term_extractor.py
→ tests/test_term_extractor.py
```

**ルール**: `src/genglossary/` 配下のモジュール構造を `tests/` 配下で再現し、ファイル名に `test_` プレフィックスを付ける。

### テスト命名規則

```python
# ✅ 良い命名（推奨）
def test_create_document_with_valid_path():
    """Test creating a document with a valid file path."""
    ...

def test_get_line_raises_error_for_invalid_index():
    """Test get_line raises IndexError for invalid index."""
    ...

def test_extract_terms_returns_empty_list_for_empty_document():
    """Test extract_terms returns empty list for empty document."""
    ...

# ❌ 悪い命名
def test1():  # 何をテストするか不明
    ...

def test_document():  # 具体性がない
    ...

def test_get_line():  # 正常系か異常系か不明
    ...
```

**命名パターン**: `test_<メソッド名>_<条件>_<期待結果>()`
- 例: `test_get_line_raises_error_for_invalid_index`

### コミットの粒度

**原則: 1つのTDDサイクル = 2つのコミット**

```bash
# ✅ 良い例（1機能 = 2コミット）
commit 1: "Add Document.get_line() tests"
commit 2: "Implement Document.get_line()"

commit 3: "Add Document.get_context() tests"
commit 4: "Implement Document.get_context()"

# ❌ 悪い例
commit 1: "Add Document model with tests and implementation"
# → テストと実装が混在

commit 1: "Add tests for Document model"
commit 2: "Implement all Document methods"
# → 複数の機能を一度に実装
```

### コミットメッセージのパターン

```bash
# テストコミット
"Add <ClassName>.<method_name>() tests"
"Add <module_name> integration tests"

# 実装コミット
"Implement <ClassName>.<method_name>()"
"Implement <feature_name>"

# リファクタリング
"Refactor <module_name> to improve readability"
"Refactor <ClassName> to use composition"

# バグ修正
"Fix <issue_description> in <module_name>"
```

詳しくは [良い/悪いコミット例](@.claude/rules/examples/good-bad-commits.md) を参照。

## TDDサイクル チェックリスト

各TDDサイクルで以下を確認してください:

### Redフェーズ
- [ ] テストを先に書いた
- [ ] テストを実行して失敗を確認した
- [ ] 失敗の理由が正しい（ImportError, AttributeError など）
- [ ] テストのみを `git add` した
- [ ] 「Add ... tests」形式でコミットした

### Greenフェーズ
- [ ] 最小限の実装でテストをパスさせた
- [ ] すべてのテストがパスすることを確認した
- [ ] 実装のみを `git add` した
- [ ] 「Implement ...」形式でコミットした

### Refactorフェーズ（必要に応じて）
- [ ] リファクタリング後もテストがパスする
- [ ] 「Refactor ...」形式でコミットした

## よくある間違い

### ❌ テストを書かずに実装を始める
```python
# NG: いきなり実装を書く
class Document(BaseModel):
    file_path: str
    content: str
```

**正しい順序**: テスト → 失敗確認 → コミット → 実装

### ❌ テストと実装を同時にコミット
```bash
$ git add tests/ src/
$ git commit -m "Add Document model"
```

**正しい方法**: 2回に分けてコミット

### ❌ 過剰な実装
テストで要求されていない機能まで実装してしまう。

**原則**: YAGNI（You Aren't Gonna Need It）を守る

### ❌ テストの失敗を確認しない
テストを書いてすぐに実装に進んでしまう。

**重要**: 必ず Red（失敗）を確認してからGreen（成功）に進む

## 詳細な実装例

完全なTDDサイクルの例は [TDDサイクル例](@.claude/rules/examples/tdd-cycle-example.md) を参照してください。

## 関連ドキュメント

- [Gitワークフロー](@.claude/rules/02-git-workflow.md) - コミット規約、ブランチ戦略
- [テスト戦略](@.claude/rules/05-testing-strategy.md) - カバレッジ、モック戦略
- [良い/悪いコミット例](@.claude/rules/examples/good-bad-commits.md) - コミットメッセージのベストプラクティス
