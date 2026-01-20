# DB更新コマンド強化計画

## 背景

先日のSQLite対応（ticket: 260118-024004）により、用語集生成の中間データをDBに保存できるようになりました。しかし、現在の設計には以下の課題があります：

- `generate` コマンドのDB保存がオプション（`--db-path`指定時のみ）
- `update` コマンドは1件ずつ手動編集のみ
- 特定のステップだけを再実行してDB更新することができない
- `runs` テーブルによる実行履歴管理が不要な複雑さを生んでいる

## 目標

1. **DB保存を必須化**: `generate` コマンド実行時は常にDBに保存（デフォルト: ./genglossary.db）
2. **再生成コマンドの追加**: `regenerate` サブコマンドで各テーブルをLLM/ファイル読み込みから再生成
3. **スキーマ簡素化**: `runs` テーブルを廃止し、単一データセットのみ管理

## 決定事項

- **コマンド名**: `regenerate` を採用（既存 `update` と明確に区別）
- **DB保存**: デフォルトで必須（./genglossary.db）、`--no-db` フラグで無効化可能
- **runs廃止**: 実行履歴管理をやめ、常に単一データセットを保持（再生成時は上書き）

## コマンド設計

```bash
# 手動編集（既存コマンド維持、--run-id不要に）
genglossary db terms update <term_id> --text "..." --category "..."
genglossary db provisional update <term_id> --definition "..." --confidence 0.9

# 全件再生成（新規コマンド、--run-id不要）
genglossary db terms regenerate --input ./target_docs
genglossary db provisional regenerate --llm-provider ollama --model llama3
genglossary db issues regenerate --llm-provider ollama --model llama3
genglossary db refined regenerate --llm-provider ollama --model llama3
```

## 実装計画

### Phase 1: スキーマ変更（runsテーブル廃止）

**変更点:**
- `runs` テーブルを削除
- 各テーブルから `run_id` 外部キーを削除
- 各テーブルにメタデータカラム追加（input_path, llm_provider, llm_model, created_at）
- スキーマバージョンを v2 にアップ

**新スキーマ:**
```sql
-- documents: ドキュメント情報
CREATE TABLE documents (
    id INTEGER PRIMARY KEY,
    file_path TEXT NOT NULL UNIQUE,
    content_hash TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- terms_extracted: 抽出用語
CREATE TABLE terms_extracted (
    id INTEGER PRIMARY KEY,
    term_text TEXT NOT NULL UNIQUE,
    category TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- glossary_provisional: 暫定用語集
CREATE TABLE glossary_provisional (
    id INTEGER PRIMARY KEY,
    term_name TEXT NOT NULL UNIQUE,
    definition TEXT NOT NULL,
    confidence REAL DEFAULT 0.0,
    occurrences TEXT DEFAULT '[]',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- glossary_issues: 精査結果
CREATE TABLE glossary_issues (
    id INTEGER PRIMARY KEY,
    term_name TEXT NOT NULL,
    issue_type TEXT NOT NULL,
    description TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- glossary_refined: 最終用語集
CREATE TABLE glossary_refined (
    id INTEGER PRIMARY KEY,
    term_name TEXT NOT NULL UNIQUE,
    definition TEXT NOT NULL,
    confidence REAL DEFAULT 0.0,
    occurrences TEXT DEFAULT '[]',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- metadata: 実行情報（単一レコード）
CREATE TABLE metadata (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    input_path TEXT,
    llm_provider TEXT,
    llm_model TEXT,
    last_updated TEXT DEFAULT CURRENT_TIMESTAMP
);
```

**影響ファイル:**
- `src/genglossary/db/schema.py`

### Phase 2: Repository層の更新

**変更内容:**

| Repository | 変更 |
|---|---|
| run_repository.py | **削除** |
| document_repository.py | run_id パラメータ削除、list_all追加 |
| term_repository.py | run_id 削除、delete_all追加 |
| provisional_repository.py | run_id 削除、delete_all追加 |
| issue_repository.py | run_id 削除、delete_all追加 |
| refined_repository.py | run_id 削除、delete_all追加 |
| metadata_repository.py | **新規** - メタデータCRUD |

### Phase 3: CLI更新

**変更点:**
- `db runs` サブコマンドグループを削除
- 全コマンドから `--run-id` オプションを削除
- `generate` コマンドでDB保存をデフォルト有効化
- `db info` コマンド追加（metadata表示）

**新しいCLI構造:**
```
db (group)
├── init                          # DB初期化
├── info                          # メタデータ表示（NEW）
├── terms (group)
│   ├── list                      # 一覧（--run-id不要）
│   ├── show <term_id>
│   ├── update <term_id>
│   ├── delete <term_id>
│   ├── import --file <path>
│   └── regenerate --input <dir>  # NEW
├── provisional (group)
│   ├── list
│   ├── show <term_id>
│   ├── update <term_id>
│   └── regenerate [--llm-provider] [--model]  # NEW
├── issues (group)
│   ├── list                      # NEW
│   └── regenerate [--llm-provider] [--model]  # NEW
└── refined (group)
    ├── list
    ├── show <term_id>
    ├── update <term_id>
    ├── export-md --output <path>
    └── regenerate [--llm-provider] [--model]  # NEW
```

### Phase 4: regenerate コマンドの実装

**各コマンドの処理フロー:**

#### `terms regenerate --input <dir>`
1. 既存用語を全削除
2. inputディレクトリからドキュメント読み込み
3. TermExtractor で用語抽出（LLM使用）
4. terms_extracted に保存
5. documents テーブル更新
6. metadata 更新

#### `provisional regenerate --llm-provider ... --model ...`
1. 既存暫定用語を全削除
2. terms_extracted から用語リスト取得
3. documents テーブルからドキュメント読み込み
4. GlossaryGenerator で用語集生成
5. glossary_provisional に保存
6. metadata 更新

#### `issues regenerate --llm-provider ... --model ...`
1. 既存issueを全削除
2. glossary_provisional から暫定用語集取得
3. GlossaryReviewer で精査
4. glossary_issues に保存

#### `refined regenerate --llm-provider ... --model ...`
1. 既存最終用語を全削除
2. glossary_provisional, glossary_issues, documents から取得
3. GlossaryRefiner で改善
4. glossary_refined に保存
5. metadata 更新

### Phase 5: generate コマンドのDB保存必須化

**変更点:**
- `--db-path` をデフォルト `./genglossary.db` に変更
- `--no-db` フラグ追加でDB保存スキップ可能
- run_id 関連コードを削除

### Phase 6: テスト・ドキュメント

- 既存テストの修正（run_id関連削除）
- regenerate コマンドのテスト追加
- README更新
- アーキテクチャドキュメント更新

## 変更対象ファイル

```
src/genglossary/
├── cli.py                         # generate の --db-path 必須化、run_id削除
├── cli_db.py                      # runs削除、regenerate追加、--run-id削除
└── db/
    ├── __init__.py                # run_repository のexport削除
    ├── schema.py                  # スキーマv2、runsテーブル削除
    ├── run_repository.py          # 削除
    ├── metadata_repository.py     # 新規
    ├── document_repository.py     # run_id削除、list_all追加
    ├── term_repository.py         # run_id削除、delete_all追加
    ├── provisional_repository.py  # run_id削除、delete_all追加
    ├── issue_repository.py        # run_id削除、delete_all追加
    └── refined_repository.py      # run_id削除、delete_all追加

tests/
├── db/
│   ├── conftest.py                # fixture更新
│   ├── test_schema.py             # v2スキーマテスト
│   ├── test_run_repository.py     # 削除
│   ├── test_metadata_repository.py # 新規
│   ├── test_document_repository.py # run_id削除
│   ├── test_term_repository.py     # run_id削除
│   ├── test_provisional_repository.py # run_id削除
│   ├── test_issue_repository.py    # run_id削除
│   └── test_refined_repository.py  # run_id削除
└── test_cli_db.py                  # runs削除、regenerateテスト追加

docs/
├── README.md                       # コマンド例更新
└── .claude/rules/03-architecture.md # スキーマ更新
```

## 検証方法

### 1. generate コマンドのDB保存必須化

```bash
# デフォルトでDB保存されることを確認
uv run genglossary generate --input ./target_docs --output ./output/glossary.md
ls -la ./genglossary.db  # ファイルが作成される

# --no-db でDB保存をスキップできることを確認
uv run genglossary generate --input ./target_docs --output ./output/glossary.md --no-db

# カスタムパスを指定できることを確認
uv run genglossary generate --input ./target_docs --output ./output/glossary.md --db-path ./custom.db

# DB情報確認
uv run genglossary db info
```

### 2. regenerate コマンド

```bash
# 事前に generate 実行
uv run genglossary generate --input ./target_docs --output ./output/glossary.md

# terms regenerate（用語を再抽出）
uv run genglossary db terms regenerate --input ./target_docs
uv run genglossary db terms list  # 更新された用語を確認

# provisional regenerate (Ollama)
uv run genglossary db provisional regenerate --llm-provider ollama --model llama3
uv run genglossary db provisional list

# provisional regenerate (OpenAI互換API)
uv run genglossary db provisional regenerate \
  --llm-provider openai --openai-base-url http://localhost:8080/v1 --model local-model

# issues regenerate
uv run genglossary db issues regenerate --llm-provider ollama --model llama3
uv run genglossary db issues list

# refined regenerate
uv run genglossary db refined regenerate --llm-provider ollama --model llama3
uv run genglossary db refined list

# 最終結果をMarkdownにエクスポート
uv run genglossary db refined export-md --output ./output/glossary_updated.md
```

### 3. 自動テスト

```bash
# 全テストを実行
uv run pytest

# 型チェック
uv run pyright
```
