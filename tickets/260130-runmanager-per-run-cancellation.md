---
priority: 2
tags: [improvement, backend, threading]
description: "RunManager: Implement per-run cancellation instead of global"
created_at: "2026-01-30T21:15:00Z"
started_at: null
closed_at: null
---

# RunManager: Implement per-run cancellation instead of global

## 概要

現在 `RunManager` は単一のグローバル `_cancel_event` を使用しており、すべての実行に同じイベントが渡されます。これにより、キャンセルが意図しない実行に影響を与える可能性があります。

## 現状の問題

### codex MCP レビューからの指摘 (High Priority)

**場所**: `src/genglossary/runs/manager.py:50, 93-99, 124-128, 167-178`

`RunManager` は単一の `_cancel_event` を保持し、すべての `ExecutionContext` に渡しています。`cancel_run()` は `run_id` を無視してイベントをセットします。

**問題点**:
- 2つの実行が重複した場合（並行 `start_run()` 呼び出しまたは複数プロセス）、一方をキャンセルするとすべてがキャンセルされる
- 終了した実行への遅延キャンセルが、新しく開始した実行をキャンセルする可能性がある

## 提案する解決策

Run ごとに個別のキャンセルトークンを管理する：

```python
class RunManager:
    def __init__(self, ...):
        # ...
        self._cancel_events: dict[int, Event] = {}
        self._cancel_events_lock = Lock()

    def start_run(self, scope: str, triggered_by: str = "api") -> int:
        # ...
        cancel_event = Event()
        with self._cancel_events_lock:
            self._cancel_events[run_id] = cancel_event
        # ...

    def cancel_run(self, run_id: int) -> None:
        with self._cancel_events_lock:
            if run_id in self._cancel_events:
                self._cancel_events[run_id].set()
        # ...
```

## 影響範囲

- `src/genglossary/runs/manager.py`
- テスト

## Tasks

- [ ] 設計レビュー・承認
- [ ] 実装
- [ ] テストの更新
- [ ] Commit
- [ ] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [ ] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket.
- [ ] Code review by codex MCP. If the issue is not addressed immediately, create a ticket.
- [ ] Update docs/architecture/*.md
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## Notes

- 260130-executor-threading-safety チケットの codex MCP レビューで High 優先度として指摘
- 現状 RunManager は1プロジェクトで1アクティブRunのみ許可しているため、実際には問題が顕在化しにくい
