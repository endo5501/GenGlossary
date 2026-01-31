---
priority: 1
tags: [refactoring, backend, db]
description: "Refactor batch insert functions to use common helper"
created_at: "2026-01-31T05:07:58Z"
started_at: 2026-01-31T12:46:46Z
closed_at: 2026-01-31T12:57:32Z
---

# Refactor batch insert functions to use common helper

## 概要

6つのバッチ挿入関数（create_terms_batch, create_documents_batch, create_issues_batch, create_glossary_terms_batch, create_provisional_terms_batch, create_refined_terms_batch）が同じパターンを持っているため、共通ヘルパー関数に統一する。

## 現状の問題

すべてのバッチ関数が以下の同じパターンを持つ:
```python
def create_XXX_batch(conn, items):
    if not items:
        return

    cursor = conn.cursor()
    cursor.executemany(
        """INSERT INTO table_name (...) VALUES (?, ...)""",
        items,
    )
```

## 提案する解決策

共通の `_batch_insert` ヘルパー関数を作成:
```python
def _batch_insert(
    conn: sqlite3.Connection,
    table_name: str,
    columns: list[str],
    data: Sequence[tuple],
) -> None:
    if not data:
        return
    placeholders = ", ".join("?" * len(columns))
    columns_str = ", ".join(columns)
    cursor = conn.cursor()
    cursor.executemany(
        f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})",
        data,
    )
```

## Tasks

- [x] _batch_insert ヘルパー関数を設計・実装
- [x] 既存バッチ関数をヘルパー使用に変更
- [x] テスト
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Update docs/architecture/*.md
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing

## Notes

- code-simplifier agent からの提案
- 260130-executor-batch-insert チケットのフォローアップ

## 完了サマリー

### 実装内容
1. `src/genglossary/db/db_helpers.py` に `batch_insert` ヘルパー関数を新規作成
2. 6つの既存バッチ関数をヘルパー使用にリファクタリング
3. 型の一貫性向上（`list` → `Sequence`）
4. セキュリティに関するdocstring追加
5. アーキテクチャドキュメント更新

### コミット
- `4bbc3b6` Add tests for batch_insert helper function
- `7ddc075` Implement batch_insert helper function
- `6194a8b` Refactor batch insert functions to use common helper
- `1157c53` Improve type consistency in batch insert functions
- `04fed90` Add security and usage notes to batch_insert docstring
- `a61b666` Update architecture docs for batch_insert helper

### 結果
- pyright: 0 errors
- pytest: 901 passed
- コード削減: -44行 / +15行
