---
priority: 3
tags: [improvement, backend, threading]
description: "RunManager: Synchronize start_run to prevent race conditions"
created_at: "2026-01-30T21:15:00Z"
started_at: 2026-01-31T13:41:52Z
closed_at: 2026-01-31T13:51:46Z
---

# RunManager: Synchronize start_run to prevent race conditions

## 概要

`start_run()` メソッドはアクティブ実行のチェックとDB操作が同期されておらず、競合状態が発生する可能性があります。

## 現状の問題

### codex MCP レビューからの指摘 (Medium Priority)

**場所**: `src/genglossary/runs/manager.py:69-99`

`start_run()` は同期されておらず、「1つのアクティブ実行のみ」チェックがアトミックではありません。

**問題点**:
- 2つのスレッドが同時に `get_active_run()` をパスし、並行実行を作成する可能性がある
- 同じ `_cancel_event` とログインフラストラクチャを共有することになる

## 提案する解決策

`start_run()` に排他ロックを追加：

```python
class RunManager:
    def __init__(self, ...):
        # ...
        self._start_run_lock = Lock()

    def start_run(self, scope: str, triggered_by: str = "api") -> int:
        with self._start_run_lock:
            # Check if a run is already active
            with self._db_connection() as conn:
                active_run = get_active_run(conn)
                if active_run is not None:
                    raise RuntimeError(f"Run already running: {active_run['id']}")

                # Create run record atomically
                run_id = create_run(conn, scope=scope, triggered_by=triggered_by)

            # ... rest of the method
```

また、DBレベルでの制約（アクティブ実行は1つのみ）を追加することも検討。

## 影響範囲

- `src/genglossary/runs/manager.py`
- テスト

## Tasks

- [x] 設計レビュー・承認
- [x] 実装
- [x] テストの更新（並行 `start_run()` テストの追加）
- [x] Commit
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
  - フォローアップチケット作成: `260131-134730-runmanager-start-run-state-consistency`
- [x] Update docs/architecture/*.md
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing

## Notes

- 260130-executor-threading-safety チケットの codex MCP レビューで Medium 優先度として指摘
- 現状は主にWebサーバーからの単一リクエストで使用されるため、実際には問題が顕在化しにくい
