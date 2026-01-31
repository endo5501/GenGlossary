---
priority: 2
tags: [improvement, backend, debugging]
description: "RunManager: Include traceback in error logging"
created_at: "2026-01-30T23:30:00+09:00"
started_at: 2026-01-31T00:37:49Z
closed_at: 2026-01-31T00:46:33Z
---

# RunManager: Include traceback in error logging

## 概要

例外発生時に `str(e)` のみが記録され、トレースバックが含まれないためデバッグが困難。

## codex MCP レビューからの指摘 (Low Priority)

**場所**: `src/genglossary/runs/manager.py:147`

Exceptions are recorded as `str(e)` only (no traceback), which reduces debuggability and may hide root causes.

## 提案する解決策

トレースバックをログに含める：

```python
import traceback

except Exception as e:
    error_traceback = traceback.format_exc()
    with transaction(conn):
        update_run_status(
            conn,
            run_id,
            "failed",
            finished_at=datetime.now(),
            error_message=str(e),
        )
    # Log with full traceback for debugging
    self._broadcast_log(run_id, {
        "run_id": run_id,
        "level": "error",
        "message": f"Run failed: {str(e)}",
        "traceback": error_traceback,  # Include traceback
    })
```

## 影響範囲

- `src/genglossary/runs/manager.py`
- フロントエンドのログ表示（traceback フィールドの表示を検討）

## Tasks

- [x] 設計レビュー・承認
- [x] 実装
- [x] テストの更新
- [x] Commit
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket.
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket.
- [x] Update docs/architecture/*.md
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing
