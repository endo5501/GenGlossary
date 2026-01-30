---
priority: 1
tags: [improvement, backend, error-handling]
description: "RunManager: Improve connection error handling in _execute_run"
created_at: "2026-01-30T23:30:00+09:00"
started_at: null
closed_at: null
---

# RunManager: Improve connection error handling in _execute_run

## 概要

`_execute_run` メソッドで `get_connection` が `try/finally` ブロックの外にあり、接続作成時にエラーが発生した場合、クリーンアップが行われない問題。

## codex MCP レビューからの指摘 (Medium Priority)

**場所**: `src/genglossary/runs/manager.py:99`

`get_connection` is outside the `try/finally`; if it raises, the thread exits before cleanup, leaving a dangling cancel event and no completion signal/status update.

## 提案する解決策

接続作成を `try` ブロック内に移動し、`finally` で適切にクリーンアップする：

```python
def _execute_run(self, run_id: int, scope: str) -> None:
    conn = None
    try:
        conn = get_connection(self.db_path)
        # ... execution logic ...
    except Exception as e:
        # ... error handling ...
    finally:
        # Cleanup cancel event
        with self._cancel_events_lock:
            self._cancel_events.pop(run_id, None)
        # Send completion signal
        self._broadcast_log(run_id, {"run_id": run_id, "complete": True})
        # Close connection if opened
        if conn is not None:
            conn.close()
```

## 影響範囲

- `src/genglossary/runs/manager.py`

## Tasks

- [ ] 設計レビュー・承認
- [ ] 実装
- [ ] テストの更新
- [ ] Commit
- [ ] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest`) before reviwing and pass all tests (No exceptions)
- [ ] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket.
- [ ] Code review by codex MCP. If the issue is not addressed immediately, create a ticket.
- [ ] Update docs/architecture/*.md
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing
