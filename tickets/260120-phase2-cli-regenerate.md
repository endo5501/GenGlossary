---
priority: 2
tags: [cli, regenerate]
description: "Phase 3-4: CLI更新とregenerateコマンド実装"
created_at: "2026-01-20T02:05:50Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# Phase 3-4: CLI更新とregenerateコマンド実装

親チケット: 260120-020550-db-regenerate-commands
依存: 260120-phase1-schema-repository

## 概要

`db runs` サブコマンドグループを削除し、全コマンドから `--run-id` オプションを削除します。また、新しい `regenerate` サブコマンドを各グループに追加します。

## Phase 3: CLI更新

### 変更点

- `db runs` サブコマンドグループを削除
- 全コマンドから `--run-id` オプションを削除
- `db info` コマンド追加（metadata表示）
- `db issues list` コマンド追加

### 削除するコマンド

```bash
# 以下のコマンドを削除
genglossary db runs list
genglossary db runs show <run_id>
genglossary db runs latest
```

### 更新するコマンド

```bash
# --run-id オプションを削除
genglossary db terms list              # Before: --run-id <id>
genglossary db provisional list        # Before: --run-id <id>
genglossary db refined list            # Before: --run-id <id>
```

### 新規コマンド

```bash
# メタデータ表示
genglossary db info

# Issues一覧表示
genglossary db issues list
```

### 新しいCLI構造

```
db (group)
├── init                          # DB初期化
├── info                          # メタデータ表示（NEW）
├── terms (group)
│   ├── list                      # 一覧（--run-id不要）
│   ├── show <term_id>
│   ├── update <term_id>
│   ├── delete <term_id>
│   └── import --file <path>
├── provisional (group)
│   ├── list
│   ├── show <term_id>
│   └── update <term_id>
├── issues (group)
│   └── list                      # NEW
└── refined (group)
    ├── list
    ├── show <term_id>
    ├── update <term_id>
    └── export-md --output <path>
```

### 影響ファイル

- `src/genglossary/cli_db.py`

## Phase 4: regenerate コマンドの実装

### 新規コマンド

```
db (group)
├── terms (group)
│   └── regenerate --input <dir>                     # NEW
├── provisional (group)
│   └── regenerate [--llm-provider] [--model]        # NEW
├── issues (group)
│   └── regenerate [--llm-provider] [--model]        # NEW
└── refined (group)
    └── regenerate [--llm-provider] [--model]        # NEW
```

### 各コマンドの処理フロー

#### `genglossary db terms regenerate --input <dir>`

**処理:**
1. 既存用語を全削除（`delete_all_terms()`）
2. inputディレクトリからドキュメント読み込み（`document_loader.load_document()`）
3. TermExtractor で用語抽出（LLM使用）
4. terms_extracted に保存（`create_term()`）
5. documents テーブル更新（`create_document()`）
6. metadata 更新（`upsert_metadata()`）

**オプション:**
- `--input <dir>`: 入力ディレクトリ（必須）
- `--llm-provider <provider>`: LLMプロバイダ（デフォルト: ollama）
- `--model <model>`: モデル名（デフォルト: llama3）
- `--db-path <path>`: DBパス（デフォルト: ./genglossary.db）

**実装例:**
```python
@terms_group.command("regenerate")
@click.option("--input", required=True, help="Input directory")
@click.option("--llm-provider", default="ollama", help="LLM provider")
@click.option("--model", default="llama3", help="Model name")
@click.option("--db-path", default="./genglossary.db", help="Database path")
def terms_regenerate(input: str, llm_provider: str, model: str, db_path: str) -> None:
    """Regenerate terms from documents using LLM."""
    # 実装
```

#### `genglossary db provisional regenerate [--llm-provider] [--model]`

**処理:**
1. 既存暫定用語を全削除（`delete_all_provisional()`）
2. terms_extracted から用語リスト取得（`list_all_terms()`）
3. documents テーブルからドキュメント読み込み（`list_all_documents()`）
4. GlossaryGenerator で用語集生成（LLM使用）
5. glossary_provisional に保存（`create_provisional_term()`）
6. metadata 更新（`upsert_metadata()`）

**オプション:**
- `--llm-provider <provider>`: LLMプロバイダ（デフォルト: ollama）
- `--model <model>`: モデル名（デフォルト: llama3）
- `--openai-base-url <url>`: OpenAI互換APIのベースURL（llm-provider=openai時）
- `--db-path <path>`: DBパス（デフォルト: ./genglossary.db）

**実装例:**
```python
@provisional_group.command("regenerate")
@click.option("--llm-provider", default="ollama", help="LLM provider")
@click.option("--model", default="llama3", help="Model name")
@click.option("--openai-base-url", help="OpenAI-compatible API base URL")
@click.option("--db-path", default="./genglossary.db", help="Database path")
def provisional_regenerate(
    llm_provider: str,
    model: str,
    openai_base_url: str | None,
    db_path: str
) -> None:
    """Regenerate provisional glossary from extracted terms using LLM."""
    # 実装
```

#### `genglossary db issues regenerate [--llm-provider] [--model]`

**処理:**
1. 既存issueを全削除（`delete_all_issues()`）
2. glossary_provisional から暫定用語集取得（`list_all_provisional()`）
3. GlossaryReviewer で精査（LLM使用）
4. glossary_issues に保存（`create_issue()`）

**オプション:**
- `--llm-provider <provider>`: LLMプロバイダ（デフォルト: ollama）
- `--model <model>`: モデル名（デフォルト: llama3）
- `--openai-base-url <url>`: OpenAI互換APIのベースURL（llm-provider=openai時）
- `--db-path <path>`: DBパス（デフォルト: ./genglossary.db）

#### `genglossary db refined regenerate [--llm-provider] [--model]`

**処理:**
1. 既存最終用語を全削除（`delete_all_refined()`）
2. glossary_provisional, glossary_issues, documents から取得
3. GlossaryRefiner で改善（LLM使用）
4. glossary_refined に保存（`create_refined_term()`）
5. metadata 更新（`upsert_metadata()`）

**オプション:**
- `--llm-provider <provider>`: LLMプロバイダ（デフォルト: ollama）
- `--model <model>`: モデル名（デフォルト: llama3）
- `--openai-base-url <url>`: OpenAI互換APIのベースURL（llm-provider=openai時）
- `--db-path <path>`: DBパス（デフォルト: ./genglossary.db）

### 影響ファイル

- `src/genglossary/cli_db.py`: regenerateコマンド追加

## Tasks

### Phase 3タスク

- [ ] test_cli_db.py: db runs削除、--run-id削除のテスト更新
- [ ] test_cli_db.py: db info コマンドのテスト追加（TDD）
- [ ] test_cli_db.py: db issues list コマンドのテスト追加（TDD）
- [ ] cli_db.py: db runs グループ削除
- [ ] cli_db.py: 全コマンドから --run-id オプション削除
- [ ] cli_db.py: db info コマンド実装
- [ ] cli_db.py: db issues list コマンド実装
- [ ] テスト実行して成功を確認
- [ ] Code simplification review using code-simplifier agent
- [ ] Update .claude/rules/03-architecture.md
- [ ] Phase 3をコミット

### Phase 4タスク

- [ ] test_cli_db.py: terms regenerate のテスト追加（TDD）
- [ ] cli_db.py: terms regenerate 実装
- [ ] test_cli_db.py: provisional regenerate のテスト追加（TDD）
- [ ] cli_db.py: provisional regenerate 実装
- [ ] test_cli_db.py: issues regenerate のテスト追加（TDD）
- [ ] cli_db.py: issues regenerate 実装
- [ ] test_cli_db.py: refined regenerate のテスト追加（TDD）
- [ ] cli_db.py: refined regenerate 実装
- [ ] 全テスト実行して成功を確認
- [ ] Phase 4をコミット

### 最終確認

- [ ] Run static analysis (`pyright`)
- [ ] Run tests (`uv run pytest`)
- [ ] Get developer approval

## 検証方法

### Phase 3検証

```bash
# DB初期化とinfo表示
uv run genglossary db init --db-path ./test.db
uv run genglossary db info --db-path ./test.db

# terms list（--run-id不要）
uv run genglossary db terms list --db-path ./test.db

# issues list
uv run genglossary db issues list --db-path ./test.db

# runs コマンドが削除されていることを確認
uv run genglossary db runs list  # エラーになるはず
```

### Phase 4検証

```bash
# 事前にgenerateを実行してDBを作成
uv run genglossary generate --input ./target_docs --output ./output/glossary.md

# terms regenerate
uv run genglossary db terms regenerate --input ./target_docs
uv run genglossary db terms list

# provisional regenerate (Ollama)
uv run genglossary db provisional regenerate --llm-provider ollama --model llama3
uv run genglossary db provisional list

# provisional regenerate (OpenAI互換API)
uv run genglossary db provisional regenerate \
  --llm-provider openai --openai-base-url http://localhost:8080/v1 --model local-model
uv run genglossary db provisional list

# issues regenerate
uv run genglossary db issues regenerate --llm-provider ollama --model llama3
uv run genglossary db issues list

# refined regenerate
uv run genglossary db refined regenerate --llm-provider ollama --model llama3
uv run genglossary db refined list

# 最終結果をMarkdownにエクスポート
uv run genglossary db refined export-md --output ./output/glossary_updated.md
```

### 全体テスト

```bash
# 全テスト実行
uv run pytest tests/test_cli_db.py -v

# 型チェック
uv run pyright src/genglossary/cli_db.py
```

## Notes

- TDD厳守: 各コマンド実装前に必ずテストを作成
- regenerateコマンドは既存データを全削除してから再生成
- LLMプロバイダは ollama / openai をサポート
- OpenAI互換APIの場合は --openai-base-url でベースURLを指定
- エラーハンドリングを適切に実装（DBが存在しない、テーブルが空など）
