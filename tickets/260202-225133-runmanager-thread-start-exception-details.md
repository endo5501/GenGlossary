---
priority: 4
tags: [improvement, backend, error-handling]
description: "RunManager: capture original exception details in DB on thread start failure"
created_at: "2026-02-02T22:51:33Z"
started_at: 2026-02-08T09:30:22Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# RunManager: capture original exception details in DB on thread start failure

## 概要

codex MCP レビューで指摘された、スレッド起動失敗時の元の例外詳細がDBに保存されない問題を対処する。

## 現状の問題

`start_run()` でスレッド起動が失敗した場合、固定のエラーメッセージのみがDBに保存される：

```python
update_run_status(
    conn, run_id, "failed",
    error_message="Failed to start execution thread",  # 固定メッセージ
    finished_at=datetime.now(timezone.utc),
)
```

元の例外（`RuntimeError`, `OSError` など）の詳細が失われ、デバッグが困難になる可能性がある。

## 提案する解決策

例外の詳細を `error_message` に含める：

```python
except Exception as e:
    # ... cleanup ...
    error_msg = f"Failed to start execution thread: {e}"
    try:
        with database_connection(self.db_path) as conn:
            with transaction(conn):
                update_run_status(
                    conn, run_id, "failed",
                    error_message=error_msg,
                    finished_at=datetime.now(timezone.utc),
                )
    except Exception as db_error:
        # ...
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
- [x] Update docs (glob: "*.md" in ./docs/architecture)
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing

## Notes

- 260201-101222-runmanager-thread-start-failure-edge-cases チケットの codex MCP レビューで指摘
- 軽微な改善（優先度低め）
