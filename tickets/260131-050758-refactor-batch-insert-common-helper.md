---
priority: 1
tags: [refactoring, backend, db]
description: "Refactor batch insert functions to use common helper"
created_at: "2026-01-31T05:07:58Z"
started_at: null
closed_at: null
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

- [ ] _batch_insert ヘルパー関数を設計・実装
- [ ] 既存バッチ関数をヘルパー使用に変更
- [ ] テスト
- [ ] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest`) before reviwing and pass all tests (No exceptions)
- [ ] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Update docs/architecture/*.md
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## Notes

- code-simplifier agent からの提案
- 260130-executor-batch-insert チケットのフォローアップ
