# Gitワークフロー

## 優先度: 必須（MUST）

このプロジェクトは Git によるバージョン管理とチケットシステムによるタスク管理を採用しています。

## ブランチ戦略

### メインブランチ
- **`main`**: 本番ブランチ、常に動作する状態を維持

### フィーチャーブランチ
- **`feature/<ticket-name>`**: 各チケットに対応する作業ブランチ

### ブランチ命名規則

```bash
# ✅ 良い例
feature/251231-123014-phase1-data-models-foundation
feature/251231-123015-phase2-llm-client
feature/add-glossary-export-feature

# ❌ 悪い例
feature/test
feature/fix
my-branch
```

## チケットシステム

### チケット操作コマンド

```bash
# チケット一覧表示
bash scripts/ticket.sh list

# チケット作業開始
bash scripts/ticket.sh start <ticket-name>

# チケット完了
bash scripts/ticket.sh close
```

### チケット作業の流れ

#### 1. チケット一覧を確認

```bash
$ bash scripts/ticket.sh list

Available tickets:
  251231-123014-phase1-data-models-foundation
  251231-123015-phase2-llm-client
  251231-123015-phase3-core-logic
  251231-123016-phase4-output-cli
  251231-123016-phase5-integration-testing
```

#### 2. チケット作業を開始

```bash
$ bash scripts/ticket.sh start 251231-123014-phase1-data-models-foundation

✓ Created branch: feature/251231-123014-phase1-data-models-foundation
✓ Switched to branch: feature/251231-123014-phase1-data-models-foundation
✓ Created current-ticket.md
```

**何が起こるか**:
- `feature/<ticket-name>` ブランチが作成される
- そのブランチに自動的に切り替わる
- `current-ticket.md` ファイルが作成される（作業内容の追跡用）

#### 3. TDDサイクルで開発を進める

```bash
# TDD サイクル（詳細は 01-tdd-workflow.md を参照）
$ git add tests/
$ git commit -m "Add Document model tests"

$ git add src/
$ git commit -m "Implement Document model"
```

#### 4. チケットを完了

```bash
$ bash scripts/ticket.sh close

✓ All tests passed
✓ Merged feature/251231-123014-phase1-data-models-foundation into main
✓ Deleted feature branch
✓ Ticket completed
```

**何が起こるか**:
- テストが実行される（すべてパスする必要がある）
- フィーチャーブランチが `main` にマージされる
- フィーチャーブランチが削除される
- `current-ticket.md` が更新される

## コミットメッセージ規約

### 基本ルール

1. **英語で記述**: コミットメッセージは英語
2. **動詞から始める**: "Add", "Implement", "Fix", "Refactor" など
3. **現在形を使用**: "Added" ではなく "Add"
4. **簡潔に**: 1行目は50文字以内
5. **説明が必要な場合**: 空行を入れて詳細を記述

### コミットメッセージのパターン

#### ✅ 良いコミットメッセージ

```bash
# テスト追加
"Add Document model tests"
"Add OllamaClient integration tests"
"Add TermExtractor unit tests for edge cases"

# 実装
"Implement Document model"
"Implement OllamaClient with retry logic"
"Implement term extraction with morphological analysis"

# バグ修正
"Fix IndexError in Document.get_line()"
"Fix JSON parsing error in OllamaClient"
"Fix incorrect term extraction for compound words"

# リファクタリング
"Refactor glossary_generator to reduce complexity"
"Refactor Document model to use Pydantic validators"
"Refactor term_extractor to improve readability"

# 複数行の例（詳細な説明付き）
"Add Document.get_context() tests

Test cases:
- Returns line with surrounding context
- Handles document start boundary
- Handles document end boundary"

"Implement Document.get_context()

Returns the target line with surrounding context lines,
handling document boundaries correctly."
```

#### ❌ 悪いコミットメッセージ

```bash
# 曖昧・不明確
"update code"
"fix bug"
"test"
"wip"
"done"

# 日本語
"Document モデルを追加"

# 小文字始まり
"add document model"

# 過去形
"Added Document model"
"Fixed bug"

# 具体性がない
"update"
"fix"
"changes"
```

### 動詞の使い分け

| 動詞 | 用途 | 例 |
|------|------|-----|
| **Add** | 新しいファイル、機能、テストを追加 | `Add Document model tests` |
| **Implement** | 機能の実装 | `Implement OllamaClient` |
| **Fix** | バグ修正 | `Fix IndexError in get_line()` |
| **Refactor** | コードの改善（動作は変わらない） | `Refactor to reduce complexity` |
| **Update** | 既存コードの更新 | `Update dependencies to latest` |
| **Remove** | コード・ファイルの削除 | `Remove deprecated method` |
| **Rename** | ファイル・変数の名前変更 | `Rename TermExtractor to MorphologicalAnalyzer` |

詳しくは [良い/悪いコミット例](@.claude/rules/examples/good-bad-commits.md) を参照。

## Git操作の実践例

### 基本的な開発フロー

```bash
# 1. チケット開始
$ bash scripts/ticket.sh start 251231-123015-phase2-llm-client

# 2. 現在のブランチを確認
$ git branch
* feature/251231-123015-phase2-llm-client
  main

# 3. TDDサイクル1回目
$ git add tests/llm/test_ollama_client.py
$ git commit -m "Add OllamaClient tests"

$ git add src/genglossary/llm/ollama_client.py
$ git commit -m "Implement OllamaClient"

# 4. TDDサイクル2回目
$ git add tests/llm/test_ollama_client.py
$ git commit -m "Add OllamaClient.generate_structured() tests"

$ git add src/genglossary/llm/ollama_client.py
$ git commit -m "Implement OllamaClient.generate_structured()"

# 5. すべてのテストを実行
$ uv run pytest
====== 10 passed in 1.23s ======

# 6. チケット完了
$ bash scripts/ticket.sh close
```

### コミット履歴の確認

```bash
# 最近のコミットを表示
$ git log --oneline -5

a3b2c1d Implement OllamaClient.generate_structured()
9f8e7d6 Add OllamaClient.generate_structured() tests
5c4d3e2 Implement OllamaClient
1a2b3c4 Add OllamaClient tests
7e6f5a4 Refactor Document model to use field validators
```

### ✅ 良いコミット履歴の例

```
6e807b4 Refactor glossary_reviewer.py to leverage Pydantic validation
e08ff54 Refactor glossary_refiner.py to optimize algorithm complexity
9ddddeb Refactor glossary_generator.py to reduce complexity
96e3b0f Refactor morphological_analyzer.py to reduce complexity and improve efficiency
74f4fe2 Refactor cli.py to improve readability and maintainability
```

**良い点**:
- 各コミットが1つの明確な変更
- コミットメッセージが具体的
- "Refactor" という動詞で改善の意図が明確
- 何を改善したか（complexity, efficiency, readability）が明記されている

### ❌ 悪いコミット履歴の例

```
a1b2c3d update
d4e5f6g fix bug
h7i8j9k wip
l0m1n2o changes
p3q4r5s test
```

**問題点**:
- 何が変更されたか不明
- 曖昧なメッセージ
- 後で履歴を追う際に理解できない

## マージとプルリクエスト

### マージのタイミング

- **チケット完了時**: `bash scripts/ticket.sh close` が自動的にマージ
- **手動マージ**: 通常は不要（チケットシステムが管理）

### プルリクエスト（将来的に）

現在はローカル開発のみですが、将来的にチーム開発になった場合:

```bash
# ブランチをリモートにプッシュ
$ git push origin feature/251231-123015-phase2-llm-client

# GitHub/GitLab でプルリクエストを作成
# レビュー → 承認 → マージ
```

## よくある質問

### Q1: コミットメッセージを間違えた場合

```bash
# 直前のコミットメッセージを修正
$ git commit --amend -m "Correct commit message"

# 注意: すでにプッシュしている場合は避ける
```

### Q2: 間違ったファイルをコミットした場合

```bash
# 直前のコミットを取り消し（変更は保持）
$ git reset --soft HEAD~1

# ファイルを修正してから再コミット
$ git add <correct-files>
$ git commit -m "Correct commit message"
```

### Q3: ブランチを間違えた場合

```bash
# 現在のブランチを確認
$ git branch

# 正しいブランチに切り替え
$ git checkout feature/correct-branch-name
```

### Q4: main ブランチの変更を取り込みたい

```bash
# main ブランチの最新を取得
$ git checkout main
$ git pull

# フィーチャーブランチに戻って main をマージ
$ git checkout feature/your-branch
$ git merge main
```

## 関連ドキュメント

- [TDDワークフロー](@.claude/rules/01-tdd-workflow.md) - TDDサイクルの詳細
- [良い/悪いコミット例](@.claude/rules/examples/good-bad-commits.md) - 実際のコミット例集
