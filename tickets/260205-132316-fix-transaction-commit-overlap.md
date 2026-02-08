---
priority: 3
tags: [backend, database, potential-bug]
description: "Fix transaction/commit overlap in update_run_status_if_active"
created_at: "2026-02-05T13:23:16Z"
started_at: 2026-02-08T11:07:40Z # Do not modify manually
closed_at: 2026-02-08T11:25:24Z # Do not modify manually
---

# Fix transaction/commit overlap in update_run_status_if_active

## Overview

`update_run_status_if_active` calls `conn.commit()` internally, but `_try_update_status` wraps it in `transaction(conn)`. This can cause issues:

1. If a SAVEPOINT is active (nested transaction), the inner `commit()` ends the transaction
2. The outer `transaction` then fails when releasing the savepoint
3. This could trigger misleading fallback updates and double-logging

## Related Files

- `src/genglossary/db/runs_repository.py:276-330`
- `src/genglossary/runs/manager.py:441-491`

## Solution Implemented

**Option A: Remove commit from repository functions** (chosen)

- Removed `conn.commit()` from `_update_run_status_if_in_states()` and `update_run_progress()`
- Added `conn.commit()` in callers:
  - `RunManager._try_update_status()` (primary + fallback connections)
  - `PipelineExecutor._create_progress_callback()`
  - API cancel endpoint (`runs.py`)
- Codex review discovered missing commit in API cancel path — fixed with test

## Tasks

- [x] Analyze which solution is best for the codebase
- [x] Implement chosen solution
- [x] Add tests for nested transaction scenarios
- [x] Commit
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Update docs (glob: "*.md" in ./docs/architecture)
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing

## Follow-up Tickets

- `260208-112001-simplify-try-update-status-duplication` — Extract duplicated logic in `_try_update_status` and document transaction commit policy (priority: 4)

## Notes

This issue was identified during code review by Codex. Currently functional but architecturally fragile.
