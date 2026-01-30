---
priority: 1
tags: [improvement, backend, memory-leak]
description: "RunManager: Clean up subscribers after run completion"
created_at: "2026-01-30T23:30:00+09:00"
started_at: 2026-01-30T15:00:54Z
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

- [x] 設計レビュー・承認
- [x] 実装
- [x] テストの更新
- [x] Commit
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket.
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket.
- [x] Update docs/architecture/*.md (N/A - 内部実装の修正のため不要)
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing

## 実装結果

### 変更ファイル
- `src/genglossary/runs/manager.py`: `_execute_run` の finally ブロックで subscribers をクリーンアップ
- `tests/runs/test_manager.py`: 4つのテストを追加（TestRunManagerSubscriberCleanup）

### コミット
1. `5797e8d` - Add tests for subscriber cleanup after run completion
2. `4ed8d21` - Fix memory leak by cleaning up subscribers after run completion

### レビュー結果
- **code-simplifier**: 例外発生時のクリーンアップ強化を提案 → 別チケット（260130-runmanager-execute-run-refactoring）で対応予定
- **codex MCP**: Approve
