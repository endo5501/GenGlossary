# 良いコミット / 悪いコミットの例

このドキュメントでは、実際のコミット例を示し、良いコミットメッセージと悪いコミットメッセージの違いを解説します。

## 実際のプロジェクトの良いコミット例

### リファクタリングのコミット

```bash
6e807b4 Refactor glossary_reviewer.py to leverage Pydantic validation
e08ff54 Refactor glossary_refiner.py to optimize algorithm complexity
9ddddeb Refactor glossary_generator.py to reduce complexity
96e3b0f Refactor morphological_analyzer.py to reduce complexity and improve efficiency
74f4fe2 Refactor cli.py to improve readability and maintainability
```

**良い点**:
- ✅ "Refactor" で開始（動詞が明確）
- ✅ どのファイルを変更したか明記
- ✅ **何を改善したか**が具体的（complexity, efficiency, readability）
- ✅ 1つのコミットで1つの変更

### TDDサイクルのコミット例

```bash
# ✅ Red Phase（テスト追加）
a3b2c1d Add Document.get_context() tests

Test cases:
- Returns line with surrounding context
- Handles document start boundary
- Handles document end boundary

# ✅ Green Phase（実装）
5c4d3e2 Implement Document.get_context()

Returns the target line with surrounding context lines,
handling document boundaries correctly using max/min.
```

**良い点**:
- ✅ テストと実装が分離されている
- ✅ "Add ... tests" → "Implement ..." の流れが明確
- ✅ 複数行メッセージで詳細を説明

## 良いコミットメッセージのパターン

### パターン1: Add（新規追加）

```bash
# ✅ 良い例
Add Document model tests
Add OllamaClient with retry logic
Add term extraction functionality
Add glossary export to Markdown

# ❌ 悪い例
add document model  # 小文字始まり
Added tests  # 過去形
add stuff  # 何を追加したか不明
```

### パターン2: Implement（実装）

```bash
# ✅ 良い例
Implement Document.get_line()
Implement OllamaClient.generate_structured()
Implement glossary refinement with issue resolution

# ❌ 悪い例
Implemented feature  # 過去形、何の機能か不明
implement document methods  # 小文字始まり
Implementation of something  # 名詞形
```

### パターン3: Fix（バグ修正）

```bash
# ✅ 良い例
Fix IndexError in Document.get_line()
Fix JSON parsing error in OllamaClient
Fix incorrect term extraction for compound words
Fix off-by-one error in line numbering

# ❌ 悪い例
fix bug  # 何のバグか不明
Fixed  # 何を修正したか不明
fix stuff  # 曖昧
```

### パターン4: Refactor（リファクタリング）

```bash
# ✅ 良い例
Refactor glossary_generator to reduce complexity
Refactor term_extractor to eliminate code duplication
Refactor OllamaClient to improve error handling
Refactor Document model to use Pydantic validators

# ❌ 悪い例
Refactor code  # どのコードか不明
refactor  # 何をリファクタしたか不明
Refactored stuff  # 過去形、曖昧
```

### パターン5: Update（更新）

```bash
# ✅ 良い例
Update dependencies to latest versions
Update README with installation instructions
Update test fixtures to use pytest parameterize

# ❌ 悪い例
update  # 何を更新したか不明
Update stuff  # 曖昧
Updated code  # 過去形、何のコードか不明
```

### パターン6: Remove（削除）

```bash
# ✅ 良い例
Remove deprecated morphological_analyzer module
Remove unused import statements
Remove legacy term extraction logic

# ❌ 悪い例
Remove stuff  # 何を削除したか不明
remove code  # 小文字始まり、何のコードか不明
Removed  # 過去形のみ
```

## 複数行コミットメッセージ

### ✅ 良い例

```bash
git commit -m "$(cat <<'EOF'
Implement OllamaClient with retry logic

Features:
- Exponential backoff (1s, 2s, 4s)
- Maximum 3 retries
- Structured output with Pydantic validation
- JSON parsing fallback strategies

Handles httpx.HTTPError and httpx.TimeoutException.
EOF
)"
```

**構成**:
1. 1行目: 簡潔な要約（50文字以内）
2. 空行
3. 詳細な説明

### ❌ 悪い例

```bash
# 全てを1行にまとめる
git commit -m "Implement OllamaClient with retry logic and exponential backoff and structured output with Pydantic validation and JSON parsing fallback strategies and error handling for httpx errors"

# 改行がない
git commit -m "Implement OllamaClient
Features: retry logic, exponential backoff..."  # 空行なし
```

## 典型的な悪いコミットメッセージ

### ❌ 最悪の例

```bash
# 何も説明していない
update
fix
changes
wip (Work in Progress)
done
test
tmp

# 日本語（プロジェクトルールでは英語）
"Document モデルを追加"
"バグを修正"

# 曖昧
"update code"
"fix bug"
"add stuff"
"modify files"

# 小文字始まり
"add document model"
"fix error"

# 過去形
"Added Document model"
"Fixed bug"
"Implemented feature"

# 感情的・冗談
"Finally fixed this damn bug!!!"
"Why doesn't this work???"
"YOLO commit"
```

## 実践的なシナリオ

### シナリオ1: テストと実装を同時にコミット（NG）

```bash
# ❌ 悪い例（TDDルール違反）
git add tests/ src/
git commit -m "Add Document model"

# ✅ 良い例（2回に分ける）
# コミット1: テスト
git add tests/models/test_document.py
git commit -m "Add Document model tests"

# コミット2: 実装
git add src/genglossary/models/document.py
git commit -m "Implement Document model"
```

### シナリオ2: 複数の機能を1つのコミットに（NG）

```bash
# ❌ 悪い例（複数の変更を含む）
git add src/genglossary/term_extractor.py src/genglossary/glossary_generator.py
git commit -m "Add term extraction and glossary generation"

# ✅ 良い例（分割する）
# コミット1
git add tests/test_term_extractor.py
git commit -m "Add TermExtractor tests"

git add src/genglossary/term_extractor.py
git commit -m "Implement TermExtractor"

# コミット2
git add tests/test_glossary_generator.py
git commit -m "Add GlossaryGenerator tests"

git add src/genglossary/glossary_generator.py
git commit -m "Implement GlossaryGenerator"
```

### シナリオ3: バグ修正

```bash
# ❌ 悪い例
git commit -m "fix"
git commit -m "bug fix"
git commit -m "oops"

# ✅ 良い例（何を修正したか明確）
git commit -m "Fix IndexError in Document.get_line() for out-of-range indices"

git commit -m "Fix JSON parsing error when LLM returns text before JSON block"

git commit -m "Fix off-by-one error in line numbering (should be 1-based)"
```

## コミットメッセージのチェックリスト

コミット前に以下を確認:

- [ ] 動詞で始まっている（Add, Implement, Fix, Refactor, Update, Remove）
- [ ] 現在形を使用している（Added, Fixed ではない）
- [ ] 大文字で始まっている（小文字ではない）
- [ ] 何を変更したか具体的に記述している
- [ ] どのファイル・機能を変更したか明記している
- [ ] 1つのコミットで1つの変更のみ
- [ ] 50文字以内（1行目）
- [ ] 詳細が必要な場合は空行を入れて複数行で説明

## 関連ドキュメント

- [TDDワークフロー](@.claude/rules/01-tdd-workflow.md) - TDDサイクルとコミット
- [Gitワークフロー](@.claude/rules/02-git-workflow.md) - ブランチ戦略とコミット規約
