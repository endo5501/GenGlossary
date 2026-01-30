---
priority: 1
tags: [improvement, backend, race-condition]
description: "RunManager: Fix race condition between cancellation check and status update"
created_at: "2026-01-30T23:30:00+09:00"
started_at: null
closed_at: null
---

# RunManager: Fix race condition between cancellation check and status update

## 概要

`cancel_event.is_set()` チェック後、ステータス更新前にキャンセルが呼ばれた場合、run が "completed" としてマークされる可能性がある問題。

## codex MCP レビューからの指摘 (Medium Priority)

**場所**: `src/genglossary/runs/manager.py:136`

Cancellation is checked once after `executor.execute`; if `cancel_run` is called just after `cancel_event.is_set()` but before the "completed" update, the run can be marked completed despite a cancel request.

## 提案する解決策

ステータス更新直前にもう一度チェックするか、DB更新をキャンセル状態に条件付けする：

### Option A: Double check
```python
if cancel_event.is_set():
    with transaction(conn):
        cancel_run(conn, run_id)
else:
    # Check again immediately before update
    if cancel_event.is_set():
        with transaction(conn):
            cancel_run(conn, run_id)
    else:
        with transaction(conn):
            update_run_status(conn, run_id, "completed", ...)
```

### Option B: Conditional DB update
```python
# Use DB-level condition: only update to completed if not already cancelled
cursor.execute("""
    UPDATE runs SET status = 'completed', finished_at = ?
    WHERE id = ? AND status != 'cancelled'
""", (datetime.now(), run_id))
```

## 影響範囲

- `src/genglossary/runs/manager.py`
- 場合によっては `src/genglossary/db/runs_repository.py`

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
