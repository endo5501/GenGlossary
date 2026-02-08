---
priority: 3
tags: [backend, bug-prevention]
description: "Fix cross-process race condition for active run check"
created_at: "2026-02-05T23:12:26Z"
started_at: 2026-02-08T12:05:57Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# Fix cross-process race condition for active run check

## Overview

Codex review identified a cross-process race condition in `start_run`:

Two processes can both see "no active run" and insert a new run, resulting in multiple active runs.

## Related Files

- `src/genglossary/runs/manager.py:86-95` (`start_run`)

## Current Behavior

```python
with self._start_run_lock:  # In-process lock only
    with database_connection(self.db_path) as conn:
        active_run = get_active_run(conn)
        if active_run is not None:
            raise RuntimeError(...)

        with transaction(conn):
            run_id = create_run(conn, ...)
```

## Problem

- `_start_run_lock` only protects against concurrent calls within the same process
- Two separate processes can both pass the `get_active_run` check
- Both processes create a new run, violating the "one active run" constraint

## Design: BEGIN IMMEDIATE による排他制御

**採用: Option B（Immediate write lock）**

単一ユーザー想定のSQLiteアプリケーションのため、`BEGIN IMMEDIATE` トランザクションによるDBレベルの書き込みロックで十分。

### 変更内容

**1. `connection.py` に `immediate_transaction` コンテキストマネージャを追加**

既存の `transaction()` は `BEGIN DEFERRED`（SQLiteデフォルト）を使用。`BEGIN IMMEDIATE` はトランザクション開始時点で書き込みロックを取得し、他プロセスの同時書き込みトランザクションを防止する。

```python
@contextmanager
def immediate_transaction(conn: sqlite3.Connection) -> Iterator[None]:
    conn.execute("BEGIN IMMEDIATE")
    try:
        yield
        conn.commit()
    except Exception:
        conn.rollback()
        raise
```

**2. `manager.py` の `start_run` を修正**

`transaction(conn)` → `immediate_transaction(conn)` に置き換え、チェックと作成を1つの即時ロックトランザクション内で実行。

**3. `_start_run_lock` はそのまま残す**

同一プロセス内の不要なDB競合（`SQLITE_BUSY`）を避ける軽量な最適化として維持。コメントで役割を明確化。

**4. エラーハンドリング**

`BEGIN IMMEDIATE` が `busy_timeout`（5秒）以内にロック取得できない場合の `OperationalError` は、そのまま呼び出し元に伝搬（特別なハンドリング不要）。

### テスト方針

- `immediate_transaction` の単体テスト（正常コミット、例外時ロールバック）
- `start_run` の既存テストがそのまま通ることを確認
- クロスプロセステストは実装コストが高く単一ユーザー想定のため、設計意図をドキュメントで記録

## Tasks

- [x] Choose solution approach
- [ ] Add `immediate_transaction` to `connection.py` with tests (TDD)
- [ ] Update `start_run` to use `immediate_transaction`
- [ ] Update `_start_run_lock` comment
- [ ] Commit
- [ ] Run static analysis (`pyright`) before reviewing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest`) before reviewing and pass all tests (No exceptions)
- [ ] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Update docs (glob: "*.md" in ./docs/architecture)
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## Notes

Identified by codex MCP during review of ticket 260205-224243.
Low risk in current usage (single process), but important for future scalability.
Single-user SQLite application — Option B alone is sufficient.
