---
priority: 5
tags: [improvement, backend, memory-leak]
description: "RunManager: Clean up subscribers after run completion"
created_at: "2026-01-30T23:30:00+09:00"
started_at: null
closed_at: null
---

# RunManager: Clean up subscribers after run completion

## 概要

run 完了時に `_subscribers[run_id]` がクリアされないため、切断された SSE クライアントの Queue がメモリに残り続ける問題。

## codex MCP レビューからの指摘 (Medium Priority)

**場所**: `src/genglossary/runs/manager.py:202, 250`

Subscribers are only removed if clients call `unregister_subscriber`; on completion you broadcast but never clear `_subscribers[run_id]`, so abandoned SSE clients leak queues and keep the run id alive.

## 提案する解決策

`_execute_run` の `finally` ブロックで、completion signal 送信後に subscribers をクリアする：

```python
finally:
    # Cleanup cancel event for this run
    with self._cancel_events_lock:
        self._cancel_events.pop(run_id, None)
    # Send completion signal to close SSE stream
    self._broadcast_log(run_id, {"run_id": run_id, "complete": True})
    # Clear subscribers for this run
    with self._subscribers_lock:
        self._subscribers.pop(run_id, None)
    # Close the connection when thread completes
    conn.close()
```

## 影響範囲

- `src/genglossary/runs/manager.py`

## Tasks

- [ ] 設計レビュー・承認
- [ ] 実装
- [ ] テストの更新
- [ ] Commit
- [ ] Run static analysis (`pyright`) and tests before closing
