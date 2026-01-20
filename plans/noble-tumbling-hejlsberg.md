# SQLite永続化レイヤー実装プラン

## 概要

GenGlossaryにSQLite永続化レイヤーを追加し、中間データ（抽出語、暫定用語集）と最終用語集を保存できるようにする。CLIコマンドでデータの閲覧・更新を可能にする。

## ファイル構成

```
src/genglossary/
├── db/                           # 新規: DBアクセス層
│   ├── __init__.py
│   ├── connection.py             # SQLite接続管理
│   ├── schema.py                 # スキーマ定義、マイグレーション
│   ├── models.py                 # JSON シリアライズ/デシリアライズ
│   ├── run_repository.py         # runs CRUD
│   ├── document_repository.py    # documents CRUD
│   ├── term_repository.py        # terms_extracted CRUD
│   ├── provisional_repository.py # glossary_provisional CRUD
│   ├── issue_repository.py       # glossary_issues CRUD
│   └── refined_repository.py     # glossary_refined CRUD
├── cli_db.py                     # 新規: db サブコマンド群
└── cli.py                        # 修正: db グループ追加
tests/
└── db/                           # 新規: DBテスト
    ├── conftest.py
    ├── test_schema.py
    ├── test_connection.py
    ├── test_models.py
    └── test_*_repository.py
```

## SQLiteスキーマ

```sql
-- 実行履歴
CREATE TABLE runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    input_path TEXT NOT NULL,
    llm_provider TEXT NOT NULL,
    llm_model TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'running',  -- running/completed/failed
    started_at TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at TEXT,
    error_message TEXT
);

-- 入力ドキュメント
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    UNIQUE(run_id, file_path)
);

-- 機械的抽出語
CREATE TABLE terms_extracted (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    term_text TEXT NOT NULL,
    category TEXT,
    UNIQUE(run_id, term_text)
);

-- 暫定用語集
CREATE TABLE glossary_provisional (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    term_name TEXT NOT NULL,
    definition TEXT NOT NULL,
    confidence REAL DEFAULT 0.0,
    occurrences TEXT NOT NULL,  -- JSON
    UNIQUE(run_id, term_name)
);

-- 精査結果
CREATE TABLE glossary_issues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    term_name TEXT NOT NULL,
    issue_type TEXT NOT NULL,
    description TEXT NOT NULL,
    should_exclude INTEGER DEFAULT 0,
    exclusion_reason TEXT
);

-- 最終用語集
CREATE TABLE glossary_refined (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    term_name TEXT NOT NULL,
    definition TEXT NOT NULL,
    confidence REAL DEFAULT 0.0,
    occurrences TEXT NOT NULL,  -- JSON
    UNIQUE(run_id, term_name)
);
```

## CLIコマンド構造

```
genglossary db
├── init                    # DB初期化
├── runs list|show|latest   # 実行履歴
├── terms list              # 抽出語一覧
├── provisional list|show   # 暫定用語集
└── refined list|show|export-md  # 最終用語集
```

## 実装フェーズ（TDD）

### Phase 1: DBアクセス層の基盤
1. `db/schema.py` - スキーマ初期化、バージョン管理
2. `db/connection.py` - 接続管理、トランザクション
3. `db/models.py` - JSON シリアライズ/デシリアライズ
4. `db/run_repository.py` - runs CRUD

### Phase 2: 各テーブルのRepository
5. `db/document_repository.py`
6. `db/term_repository.py`
7. `db/provisional_repository.py`
8. `db/issue_repository.py`
9. `db/refined_repository.py`

### Phase 3: CLIコマンド
10. `cli_db.py` - db init
11. db runs コマンド群
12. db terms コマンド群
13. db provisional コマンド群
14. db refined コマンド群

### Phase 4: 既存フローとの統合
15. `cli.py` の generate に `--db-path` オプション追加
16. 統合テスト

## 主要な設計判断

| 項目 | 決定 | 理由 |
|------|------|------|
| occurrences保存 | JSON文字列 | 正規化より単純、Pydanticで型検証 |
| 外部キー | ON DELETE CASCADE | run削除時に関連データ自動削除 |
| DB保存 | オプショナル | 既存フロー維持、`--db-path`で有効化 |
| CLI出力 | table/json形式 | richでテーブル表示、パイプライン連携 |

## 検証方法

1. 各Repositoryのユニットテスト（インメモリDB使用）
2. CLIコマンドの統合テスト（CliRunner使用）
3. 完全フローテスト: generate → DB保存 → CLI参照
4. `uv run pytest` 全テストパス
5. `uv run pyright` 型チェックパス
