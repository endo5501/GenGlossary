---
priority: 2
tags: [db, schema, repository]
description: "Phase 1-2: スキーマ変更とRepository層更新（runsテーブル廃止）"
created_at: "2026-01-20T02:05:50Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# Phase 1-2: スキーマ変更とRepository層更新

親チケット: 260120-020550-db-regenerate-commands

## 概要

`runs` テーブルを廃止し、スキーマをv2に更新します。各テーブルから `run_id` を削除し、Repository層を更新します。

## Phase 1: スキーマ変更（runsテーブル廃止）

### 変更点

- `runs` テーブルを削除
- 各テーブルから `run_id` 外部キーを削除
- 各テーブルにメタデータカラム追加（created_at）
- `metadata` テーブルを新規追加（単一レコード保持）
- スキーマバージョンを v2 にアップ

### 新スキーマ (v2)

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

### スキーマバージョン管理

- `get_schema_version()` でバージョン2を返すように変更
- v1からv2への自動マイグレーション機能を追加（オプション）
  - 既存のv1 DBを検出した場合、警告を表示
  - `--force-migrate` フラグでv2に移行可能

### 影響ファイル

- `src/genglossary/db/schema.py`

## Phase 2: Repository層の更新

### 変更内容

| Repository | 変更 | 詳細 |
|-----------|------|------|
| run_repository.py | **削除** | runs テーブル廃止により不要 |
| metadata_repository.py | **新規作成** | メタデータCRUD操作 |
| document_repository.py | run_id削除 | - create_document(conn, file_path, content_hash)<br>- list_all_documents(conn)<br>- get_document_by_path(conn, file_path) |
| term_repository.py | run_id削除 | - create_term(conn, term_text, category)<br>- list_all_terms(conn)<br>- delete_all_terms(conn) |
| provisional_repository.py | run_id削除 | - create_provisional_term(conn, term_name, definition, confidence, occurrences)<br>- list_all_provisional(conn)<br>- delete_all_provisional(conn) |
| issue_repository.py | run_id削除 | - create_issue(conn, term_name, issue_type, description)<br>- list_all_issues(conn)<br>- delete_all_issues(conn) |
| refined_repository.py | run_id削除 | - create_refined_term(conn, term_name, definition, confidence, occurrences)<br>- list_all_refined(conn)<br>- delete_all_refined(conn) |

### 新規: metadata_repository.py

```python
"""メタデータ管理Repository"""
import sqlite3
from typing import Optional
from datetime import datetime


def get_metadata(conn: sqlite3.Connection) -> Optional[sqlite3.Row]:
    """メタデータを取得（1レコードのみ）"""
    cursor = conn.execute("SELECT * FROM metadata WHERE id = 1")
    return cursor.fetchone()


def upsert_metadata(
    conn: sqlite3.Connection,
    input_path: Optional[str] = None,
    llm_provider: Optional[str] = None,
    llm_model: Optional[str] = None
) -> None:
    """メタデータを作成/更新（UPSERTパターン）"""
    conn.execute(
        """
        INSERT INTO metadata (id, input_path, llm_provider, llm_model, last_updated)
        VALUES (1, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            input_path = COALESCE(?, input_path),
            llm_provider = COALESCE(?, llm_provider),
            llm_model = COALESCE(?, llm_model),
            last_updated = ?
        """,
        (
            input_path, llm_provider, llm_model, datetime.now().isoformat(),
            input_path, llm_provider, llm_model, datetime.now().isoformat()
        )
    )
    conn.commit()


def clear_metadata(conn: sqlite3.Connection) -> None:
    """メタデータをクリア"""
    conn.execute("DELETE FROM metadata WHERE id = 1")
    conn.commit()
```

### __init__.py の更新

```python
# src/genglossary/db/__init__.py
from genglossary.db.connection import get_connection, database_connection
from genglossary.db.schema import initialize_db, get_schema_version
# run_repository を削除
from genglossary.db.metadata_repository import (
    get_metadata,
    upsert_metadata,
    clear_metadata
)
from genglossary.db.document_repository import (
    create_document,
    list_all_documents,
    get_document_by_path
)
from genglossary.db.term_repository import (
    create_term,
    list_all_terms,
    get_term_by_id,
    update_term,
    delete_term,
    delete_all_terms
)
from genglossary.db.provisional_repository import (
    create_provisional_term,
    list_all_provisional,
    get_provisional_by_id,
    update_provisional_term,
    delete_all_provisional
)
from genglossary.db.issue_repository import (
    create_issue,
    list_all_issues,
    delete_all_issues
)
from genglossary.db.refined_repository import (
    create_refined_term,
    list_all_refined,
    get_refined_by_id,
    update_refined_term,
    delete_all_refined,
    export_refined_to_markdown
)

__all__ = [
    # connection
    "get_connection",
    "database_connection",
    # schema
    "initialize_db",
    "get_schema_version",
    # metadata
    "get_metadata",
    "upsert_metadata",
    "clear_metadata",
    # document
    "create_document",
    "list_all_documents",
    "get_document_by_path",
    # term
    "create_term",
    "list_all_terms",
    "get_term_by_id",
    "update_term",
    "delete_term",
    "delete_all_terms",
    # provisional
    "create_provisional_term",
    "list_all_provisional",
    "get_provisional_by_id",
    "update_provisional_term",
    "delete_all_provisional",
    # issue
    "create_issue",
    "list_all_issues",
    "delete_all_issues",
    # refined
    "create_refined_term",
    "list_all_refined",
    "get_refined_by_id",
    "update_refined_term",
    "delete_all_refined",
    "export_refined_to_markdown",
]
```

## Tasks

### Phase 1タスク

- [ ] test_schema.py: v2スキーマのテスト作成（TDD）
- [ ] schema.py: v2スキーマ実装
- [ ] テスト実行して成功を確認
- [ ] Phase 1をコミット

### Phase 2タスク

- [ ] test_metadata_repository.py: メタデータRepositoryテスト作成（TDD）
- [ ] metadata_repository.py: 実装
- [ ] test_document_repository.py: run_id削除、list_all追加のテスト
- [ ] document_repository.py: run_id削除、list_all実装
- [ ] test_term_repository.py: run_id削除、delete_all追加のテスト
- [ ] term_repository.py: run_id削除、delete_all実装
- [ ] test_provisional_repository.py: run_id削除、delete_all追加のテスト
- [ ] provisional_repository.py: run_id削除、delete_all実装
- [ ] test_issue_repository.py: run_id削除、delete_all追加のテスト
- [ ] issue_repository.py: run_id削除、delete_all実装
- [ ] test_refined_repository.py: run_id削除、delete_all追加のテスト
- [ ] refined_repository.py: run_id削除、delete_all実装
- [ ] test_run_repository.py: 削除
- [ ] run_repository.py: 削除
- [ ] __init__.py: export更新
- [ ] tests/db/conftest.py: fixture更新（run_id削除）
- [ ] 全テスト実行して成功を確認
- [ ] Code simplification review using code-simplifier agent
- [ ] Update .claude/rules/03-architecture.md
- [ ] Phase 2をコミット

### 最終確認

- [ ] Run static analysis (`pyright`)
- [ ] Run tests (`uv run pytest`)
- [ ] Get developer approval

## 検証方法

```bash
# スキーマv2が作成されることを確認
python -c "
from genglossary.db import get_connection, initialize_db, get_schema_version
conn = get_connection(':memory:')
initialize_db(conn)
print(f'Schema version: {get_schema_version(conn)}')
assert get_schema_version(conn) == 2
print('✓ Schema v2 created successfully')
"

# メタデータ操作の確認
python -c "
from genglossary.db import get_connection, initialize_db
from genglossary.db import upsert_metadata, get_metadata
conn = get_connection(':memory:')
initialize_db(conn)
upsert_metadata(conn, input_path='./test', llm_provider='ollama', llm_model='llama3')
meta = get_metadata(conn)
assert meta['input_path'] == './test'
print('✓ Metadata operations work correctly')
"

# Repository操作の確認（run_id不要）
python -c "
from genglossary.db import get_connection, initialize_db
from genglossary.db import create_term, list_all_terms, delete_all_terms
conn = get_connection(':memory:')
initialize_db(conn)
create_term(conn, 'test_term', 'category1')
terms = list_all_terms(conn)
assert len(terms) == 1
delete_all_terms(conn)
terms = list_all_terms(conn)
assert len(terms) == 0
print('✓ Repository operations work without run_id')
"

# 全テスト実行
uv run pytest tests/db/

# 型チェック
uv run pyright src/genglossary/db/
```

## Notes

- TDD厳守: 各モジュール修正前に必ずテストを作成
- run_id を削除することで、コードがシンプルになる
- metadata テーブルは単一レコード（id=1固定）で管理
- 各Repositoryに delete_all_* 関数を追加（regenerateコマンドで使用）
