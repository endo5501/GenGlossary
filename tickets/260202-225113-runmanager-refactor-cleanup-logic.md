---
priority: 3
tags: [refactoring, backend, threading]
description: "RunManager: refactor cleanup logic into shared method"
created_at: "2026-02-02T22:51:13Z"
started_at: 2026-02-05T15:47:15Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# RunManager: refactor cleanup logic into shared method

## 概要

code-simplifier レビューで指摘された、cleanup処理の重複を解消する。

## 現状の問題

`start_run()` の例外ハンドラーと `_execute_run()` の finally ブロックで、以下の cleanup 処理が重複している：

1. `cancel_event` のクリーンアップ (`self._cancel_events.pop(run_id, None)`)
2. 完了シグナルのブロードキャスト (`self._broadcast_log(run_id, {"complete": True})`)
3. `subscribers` のクリーンアップ (`self._subscribers.pop(run_id, None)`)

## 提案する解決策

`_cleanup_run_resources(run_id: int)` メソッドを抽出し、両方の箇所から呼び出す。

```python
def _cleanup_run_resources(self, run_id: int) -> None:
    """Cleanup resources associated with a run."""
    with self._cancel_events_lock:
        self._cancel_events.pop(run_id, None)
    self._broadcast_log(run_id, {"run_id": run_id, "complete": True})
    with self._subscribers_lock:
        self._subscribers.pop(run_id, None)
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
- [x] Update docs/architecture/*.md (N/A - no architecture docs exist)
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing

## Notes

- 260201-101222-runmanager-thread-start-failure-edge-cases チケットの code-simplifier レビューで指摘
- 純粋なリファクタリング（機能変更なし）
