---
priority: 4
tags: [improvement, backend, threading]
description: "RunManager: Improve start_run in-memory state consistency"
created_at: "2026-01-31T13:47:30Z"
started_at: 2026-02-01T10:01:22Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# RunManager: Improve start_run in-memory state consistency

## 概要

`start_run()` メソッドでは、DB にアクティブな run を作成した後、ロックを解放してからインメモリ状態（`_current_run_id`, `_cancel_events`）を更新している。これにより、DB 状態とインメモリ状態の間に不整合ウィンドウが生じる。

## 現状の問題

### codex MCP レビューからの指摘

**場所**: `src/genglossary/runs/manager.py` (start_run)

1. **High**: `start_run` は `_start_run_lock` を解放した後で `_current_run_id` と `_cancel_events` を更新している。DB でアクティブな run が表示されているが、インメモリ状態がまだ更新されていないウィンドウがある。

2. **Medium**: ロック順序逆転リスク - `start_run` は `_start_run_lock` → `_cancel_events_lock` の順でロックを取得。他のメソッドが逆順でロックを取得するとデッドロックの可能性がある。

3. **Medium**: DB run 作成後、`_cancel_events` が設定される前に例外が発生すると、キャンセルできないアクティブな run が残る可能性がある。

## 影響範囲の分析

- `_current_run_id` は現在クラス内で読み取られていない（未使用）ため、問題は発生しない
- `_cancel_events` の競合ウィンドウは、run 開始直後（スレッド開始前）にキャンセルを試みる極めてまれなケースのみ。その場合キャンセルは単に無視される（192-193 行目の `get` が None を返す）
- ロック順序逆転リスクは現在のコードでは発生しない（`_start_run_lock` は `start_run` でのみ使用）

## 承認された設計

### 変更内容

**1. `_current_run_id` フィールドの削除**
- 未使用のため削除
- `__init__` と `start_run` から該当行を削除

**2. `_cancel_events` 設定をロック内に移動**
- DB操作と同じ `_start_run_lock` 内で `_cancel_events` を設定
- ロック順序は `_start_run_lock` → `_cancel_events_lock` で一貫

**3. 例外時クリーンアップの追加**
- スレッド起動失敗時に `_cancel_events` から削除し、DBステータスを `failed` に更新

### コード変更

```python
def start_run(self, scope: str, triggered_by: str = "api") -> int:
    with self._start_run_lock:
        # Check if a run is already active and create run record atomically
        with database_connection(self.db_path) as conn:
            active_run = get_active_run(conn)
            if active_run is not None:
                raise RuntimeError(f"Run already running: {active_run['id']}")

            with transaction(conn):
                run_id = create_run(conn, scope=scope, triggered_by=triggered_by)

        # Create cancel event within the same lock
        cancel_event = Event()
        with self._cancel_events_lock:
            self._cancel_events[run_id] = cancel_event

    # Start background thread (outside lock)
    try:
        self._thread = Thread(target=self._execute_run, args=(run_id, scope))
        self._thread.daemon = True
        self._thread.start()
    except Exception:
        # Cleanup on thread start failure
        with self._cancel_events_lock:
            self._cancel_events.pop(run_id, None)
        with database_connection(self.db_path) as conn:
            with transaction(conn):
                update_run_status(conn, run_id, "failed",
                                  error_message="Failed to start execution thread")
        raise

    return run_id
```

## Tasks

- [x] 設計レビュー・承認
- [x] 実装
- [x] テストの更新
- [x] Commit
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
  - Follow-up ticket created: `260201-101222-runmanager-thread-start-failure-edge-cases`
- [x] Update docs/architecture/*.md
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## Notes

- 260130-runmanager-start-run-synchronization チケットの codex MCP レビューで指摘
- 現状は重大な問題ではないが、将来の拡張時に問題になる可能性がある
- 優先度 4 として登録
