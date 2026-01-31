# プロンプトエスケープ統一リファクタリング計画

## 目的

code-simplifier レビューで指摘された以下の問題を修正:
1. `glossary_generator.py` の重複エスケープ関数 `_escape_context_tags()`
2. 複数ファイルでの二重エスケープ問題
3. プロンプトセキュリティのドキュメント不足

## フェーズ1: 重複関数の削除

### ステップ1.1: `_escape_context_tags` を共通ユーティリティに置き換え

**対象**: `src/genglossary/glossary_generator.py` (行266-300)

**作業内容**:
1. テスト実行で既存動作を確認
2. `_escape_context_tags()` メソッドを削除
3. `_build_context_text()` で `escape_prompt_content(occ.context, "context")` を使用
4. インポートに `escape_prompt_content` を追加
5. テスト実行、コミット

**Before**:
```python
def _escape_context_tags(self, text: str) -> str:
    text = text.replace("</context>", "&lt;/context&gt;")
    text = text.replace("<context>", "&lt;context&gt;")
    return text

def _build_context_text(self, occurrences: list[TermOccurrence]) -> str:
    ...
    lines = "\n".join(
        f"- {self._escape_context_tags(occ.context)}"
        ...
    )
```

**After**:
```python
def _build_context_text(self, occurrences: list[TermOccurrence]) -> str:
    ...
    lines = "\n".join(
        f"- {escape_prompt_content(occ.context, 'context')}"
        ...
    )
```

---

## フェーズ2: 二重エスケープ問題の解消

### ステップ2.1: `glossary_reviewer.py` (行74-90)

**問題**: 個別 `escape_prompt_content()` → `wrap_user_data()` で二重エスケープ

**修正**: 個別エスケープを削除、`wrap_user_data()` のみ使用

```python
# Before
escaped_name = escape_prompt_content(term.name, "glossary")
escaped_definition = escape_prompt_content(term.definition, "glossary")
term_lines.append(f"- {escaped_name}: {escaped_definition} ...")
wrapped_terms = wrap_user_data(terms_text, "glossary")

# After
term_lines.append(f"- {term.name}: {term.definition} ...")
wrapped_terms = wrap_user_data(terms_text, "glossary")
```

### ステップ2.2: `glossary_refiner.py` (行200-214)

**問題**: 4フィールドを個別エスケープ → `wrap_user_data()` で二重エスケープ

**修正**: 個別エスケープを削除

```python
# Before
escaped_name = escape_prompt_content(term.name, "refinement")
...
refinement_data = f"""用語: {escaped_name}..."""
wrapped_data = wrap_user_data(refinement_data, "refinement")

# After
refinement_data = f"""用語: {term.name}..."""
wrapped_data = wrap_user_data(refinement_data, "refinement")
```

### ステップ2.3: `term_extractor.py` (行724, 737-742)

**問題**: `_create_selection_prompt()` 内で個別エスケープ → `wrap_user_data()`

**修正**: 個別エスケープと関数内インポートを削除

```python
# Before
from genglossary.utils.prompt_escape import escape_prompt_content
escaped_terms = [escape_prompt_content(t, "terms") for t in terms]
classification_text += f"- {category_label}: {', '.join(escaped_terms)}\n"
wrapped_classification = wrap_user_data(classification_text, "terms")

# After
classification_text += f"- {category_label}: {', '.join(terms)}\n"
wrapped_classification = wrap_user_data(classification_text, "terms")
```

---

## フェーズ3: ドキュメント追加

### ステップ3.1: プロンプトセキュリティドキュメント作成

**新規**: `docs/architecture/prompt-security.md`

**内容**:
- エスケープユーティリティの説明
- 正しい使用パターン (`wrap_user_data()` のみ使用)
- 避けるべきパターン (二重エスケープ)
- 各プロセッサでのタグ一覧
- テスト実行方法

### ステップ3.2: README.md 更新

**修正**: `docs/architecture/README.md` のドキュメント一覧に追加

---

## 修正対象ファイル

| ファイル | 修正内容 |
|---------|---------|
| `src/genglossary/glossary_generator.py` | `_escape_context_tags()` 削除、共通ユーティリティ使用 |
| `src/genglossary/glossary_reviewer.py` | 個別エスケープ削除 |
| `src/genglossary/glossary_refiner.py` | 個別エスケープ削除 |
| `src/genglossary/term_extractor.py` | 個別エスケープ・関数内インポート削除 |
| `docs/architecture/prompt-security.md` | 新規作成 |
| `docs/architecture/README.md` | ドキュメント一覧更新 |

---

## TDDワークフロー

各ステップで以下を実施:

1. **Red確認**: `uv run pytest tests/test_<module>.py -v` で既存テスト通過確認
2. **Green**: コード修正
3. **テスト実行**: 全テスト通過確認
4. **Commit**: 変更をコミット

最終確認:
```bash
uv run pytest -v
uv run pyright src/genglossary
```

---

## 検証方法

### 単体テスト
```bash
# 各モジュールのテスト
uv run pytest tests/test_glossary_generator.py -v
uv run pytest tests/test_glossary_reviewer.py -v
uv run pytest tests/test_glossary_refiner.py -v
uv run pytest tests/test_term_extractor.py -v

# プロンプトインジェクション関連テスト
uv run pytest -k "injection" -v
```

### 統合テスト
```bash
# 全テスト実行
uv run pytest -v

# 静的解析
uv run pyright src/genglossary
```

### 動作確認
```bash
# CLIで実際に用語集生成を実行（オプション）
uv run genglossary --help
```

---

## コミット計画

1. `Refactor: Replace _escape_context_tags with shared escape_prompt_content utility`
2. `Fix: Remove double-escaping in glossary_reviewer.py`
3. `Fix: Remove double-escaping in glossary_refiner.py`
4. `Fix: Remove double-escaping in term_extractor.py`
5. `Docs: Add prompt security documentation`
