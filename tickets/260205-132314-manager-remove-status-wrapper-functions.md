---
priority: 3
tags: [backend, refactoring]
description: "Remove redundant status wrapper functions in RunManager"
created_at: "2026-02-05T13:23:14Z"
started_at: 2026-02-05T22:35:33Z # Do not modify manually
closed_at: 2026-02-05T22:46:08Z # Do not modify manually
---

# Remove redundant status wrapper functions in RunManager

## Overview

`RunManager` contains three wrapper functions that are nearly identical:
- `_try_cancel_status`
- `_try_complete_status`
- `_try_failed_status`

Each is a single-line wrapper around `_try_update_status`. These can be removed and callers can use `_try_update_status` directly.

## Related Files

- `src/genglossary/runs/manager.py:496-536`

## Current Code

```python
def _try_cancel_status(self, conn, run_id) -> bool:
    return self._try_update_status(conn, run_id, "cancelled")

def _try_complete_status(self, conn, run_id) -> bool:
    return self._try_update_status(conn, run_id, "completed")

def _try_failed_status(self, conn, run_id, error_message) -> bool:
    return self._try_update_status(conn, run_id, "failed", error_message)
```

## Proposed Change

Remove wrapper functions and call `_try_update_status` directly from `_try_status_with_fallback`.

## Benefits

- ~30 lines of code reduction
- Fewer indirect function calls
- Simpler maintenance

## Tasks

- [x] Identify all usages of wrapper functions
- [x] Update callers to use `_try_update_status` directly
- [x] Remove wrapper functions
- [x] Update tests if necessary
- [x] Commit
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
  - Created ticket: 260205-224219-consolidate-runmanager-status-methods
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
  - Created ticket: 260205-224243-runmanager-status-persistence-reliability
- [x] Update docs/architecture/*.md
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing

## Notes

This is a minor refactoring. Functionality remains unchanged.
