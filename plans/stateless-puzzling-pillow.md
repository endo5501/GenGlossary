# Phase 2: Repository層更新計画

## 概要

Phase 1で完了したスキーマv2に合わせて、Repository層を更新します。`run_id`依存を削除し、新しいAPIを提供します。

## 変更サマリー

| Repository | 変更内容 |
|-----------|---------|
| run_repository.py | **削除** |
| metadata_repository.py | **新規作成** |
| document_repository.py | run_id削除、list_all_documents追加 |
| term_repository.py | run_id削除、list_all_terms, delete_all_terms追加 |
| provisional_repository.py | run_id削除、list_all_provisional, delete_all_provisional追加 |
| issue_repository.py | run_id削除、should_exclude/exclusion_reason削除、list_all_issues, delete_all_issues追加 |
| refined_repository.py | run_id削除、list_all_refined, delete_all_refined追加 |
| models.py | GlossaryTermRowからrun_id削除 |

## 実装手順（TDDアプローチ）

### Step 1: metadata_repository.py（新規作成）

**テスト作成** `tests/db/test_metadata_repository.py`:
- TestGetMetadata: None返却（空）、データ返却
- TestUpsertMetadata: INSERT、UPDATE、created_at設定
- TestClearMetadata: レコード削除

**実装** `src/genglossary/db/metadata_repository.py`:
- `get_metadata(conn) -> Row | None`
- `upsert_metadata(conn, llm_provider, llm_model) -> None`
- `clear_metadata(conn) -> None`

### Step 2: models.py更新

**変更**: `GlossaryTermRow`から`run_id`フィールドを削除

### Step 3: document_repository.py更新

**テスト変更**:
- `create_run`依存を削除
- `list_documents_by_run` → `list_all_documents`
- `get_document_by_path`からrun_id引数を削除

**実装変更**:
- `create_document(conn, file_path, content_hash) -> int`
- `list_all_documents(conn) -> list[Row]`
- `get_document_by_path(conn, file_path) -> Row | None`

### Step 4: term_repository.py更新

**テスト変更**:
- `create_run`依存を削除
- `list_terms_by_run` → `list_all_terms`
- `delete_all_terms`テスト追加

**実装変更**:
- `create_term(conn, term_text, category) -> int`
- `list_all_terms(conn) -> list[Row]`
- `delete_all_terms(conn) -> None`

### Step 5: provisional_repository.py更新

**テスト変更**:
- `create_run`依存を削除
- `list_provisional_terms_by_run` → `list_all_provisional`
- `delete_all_provisional`テスト追加

**実装変更**:
- `create_provisional_term(conn, term_name, definition, confidence, occurrences) -> int`
- `list_all_provisional(conn) -> list[GlossaryTermRow]`
- `delete_all_provisional(conn) -> None`

### Step 6: issue_repository.py更新

**テスト変更**:
- `create_run`依存を削除
- `should_exclude`, `exclusion_reason`削除
- `list_issues_by_run` → `list_all_issues`
- `delete_all_issues`テスト追加

**実装変更**:
- `create_issue(conn, term_name, issue_type, description) -> int`
- `list_all_issues(conn) -> list[Row]`
- `delete_all_issues(conn) -> None`

### Step 7: refined_repository.py更新

**テスト変更**:
- `create_run`依存を削除
- `list_refined_terms_by_run` → `list_all_refined`
- `delete_all_refined`テスト追加

**実装変更**:
- `create_refined_term(conn, term_name, definition, confidence, occurrences) -> int`
- `list_all_refined(conn) -> list[GlossaryTermRow]`
- `delete_all_refined(conn) -> None`

### Step 8: run_repository.py削除

- `src/genglossary/db/run_repository.py` 削除
- `tests/db/test_run_repository.py` 削除

### Step 9: __init__.py更新

新しいAPIに合わせてexportを更新

### Step 10: 最終検証

- 全テスト実行
- 型チェック

## 影響ファイル

| ファイル | 操作 |
|---------|------|
| `src/genglossary/db/metadata_repository.py` | 新規作成 |
| `tests/db/test_metadata_repository.py` | 新規作成 |
| `src/genglossary/db/models.py` | 更新 |
| `tests/db/test_models.py` | 更新 |
| `src/genglossary/db/document_repository.py` | 更新 |
| `tests/db/test_document_repository.py` | 更新 |
| `src/genglossary/db/term_repository.py` | 更新 |
| `tests/db/test_term_repository.py` | 更新 |
| `src/genglossary/db/provisional_repository.py` | 更新 |
| `tests/db/test_provisional_repository.py` | 更新 |
| `src/genglossary/db/issue_repository.py` | 更新 |
| `tests/db/test_issue_repository.py` | 更新 |
| `src/genglossary/db/refined_repository.py` | 更新 |
| `tests/db/test_refined_repository.py` | 更新 |
| `src/genglossary/db/run_repository.py` | 削除 |
| `tests/db/test_run_repository.py` | 削除 |
| `src/genglossary/db/__init__.py` | 更新 |

## 検証方法

```bash
# 全DBテスト実行
uv run pytest tests/db/ -v

# 型チェック
uv run pyright src/genglossary/db/

# 動作確認
uv run python -c "
from genglossary.db import get_connection, initialize_db
from genglossary.db import upsert_metadata, get_metadata
from genglossary.db import create_term, list_all_terms, delete_all_terms
conn = get_connection(':memory:')
initialize_db(conn)

# メタデータ確認
upsert_metadata(conn, 'ollama', 'llama3.2')
meta = get_metadata(conn)
assert meta['llm_provider'] == 'ollama'
print('Metadata: OK')

# Repository確認（run_id不要）
create_term(conn, 'test_term', 'category1')
terms = list_all_terms(conn)
assert len(terms) == 1
delete_all_terms(conn)
assert len(list_all_terms(conn)) == 0
print('Repository: OK')
"
```

## コミット戦略

各Step完了後にコミット（計10コミット）:
1. `Add metadata_repository with TDD tests`
2. `Remove run_id from GlossaryTermRow TypedDict`
3. `Update document_repository to remove run_id dependency`
4. `Update term_repository to remove run_id dependency`
5. `Update provisional_repository to remove run_id dependency`
6. `Update issue_repository to remove run_id and exclusion fields`
7. `Update refined_repository to remove run_id dependency`
8. `Remove obsolete run_repository`
9. `Update db __init__.py exports for new API`
10. `Complete Phase 2: All tests passing`
