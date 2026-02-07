---
priority: 3
tags: [backend, refactoring]
description: "Consolidate status update methods in RunManager"
created_at: "2026-02-05T22:42:19Z"
started_at: 2026-02-07T03:36:42Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# Consolidate status update methods in RunManager

## Overview

The `RunManager` class has multiple status update methods that could be consolidated:

- `_try_update_status`: Core status update logic
- `_try_status_with_fallback`: Fallback connection support
- `_update_failed_status`: Failed-specific wrapper

These can be unified into a single `_update_status_with_fallback` method.

## Related Files

- `src/genglossary/runs/manager.py`

## Current Pattern

```python
# Current: multiple layers of indirection
_try_update_status(conn, run_id, status, error_message)  # Core logic
_try_status_with_fallback(conn, run_id, status_updater, operation_name)  # Fallback
_update_failed_status(conn, run_id, error_message)  # Failed wrapper
```

## Proposed Change

```python
# Unified: single method with fallback support
def _update_status_with_fallback(
    self,
    conn: sqlite3.Connection | None,
    run_id: int,
    status: str,
    error_message: str | None = None,
) -> None:
    """Update run status with automatic fallback to new connection if needed."""
```

## Benefits

- Eliminates lambda expressions in callers
- Reduces method count
- Simplifies call chain
- Clearer API

## Additional Improvements

Also consider extracting error handling pattern to `_handle_run_failure`:
- Duplicated pattern in lines 435-447 and 206-217
- Combines print, status update, and broadcast_log

## Tasks

- [x] Create unified `_update_status_with_fallback` method
- [x] Update all callers to use new method
- [x] Remove obsolete methods (`_try_status_with_fallback`, `_update_failed_status`)
- [x] Optionally extract `_handle_run_failure` helper (skipped by developer decision)
- [x] Update tests if necessary
- [x] Commit
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Update docs/architecture/*.md
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing

## Design (brainstorming result)

### Approach: Merge 3 methods → 1 (`_try_update_status`)

Extend `_try_update_status` to accept `conn: Connection | None` and incorporate
fallback logic internally. Remove `_try_status_with_fallback` and `_update_failed_status`.

### `_try_update_status` new signature

```python
def _try_update_status(
    self,
    conn: sqlite3.Connection | None,  # Extended to accept None
    run_id: int,
    status: str,
    error_message: str | None = None,
) -> bool:
```

Flow:
1. If conn is valid → try primary connection
2. If primary fails with exception → fallback to `database_connection(self.db_path)`
3. If conn is None → go directly to fallback
4. Return True on success or no-op, False only on complete failure

### Caller changes

- `_finalize_run_status`: Replace `_try_status_with_fallback(conn, rid, lambda...)` with `_try_update_status(conn, rid, status)`
- `_execute_run` outer except: Replace `_update_failed_status(conn, rid, msg)` with `_try_update_status(conn, rid, "failed", msg)`
- Remove `Callable` import (no more lambdas)

### Removed methods

- `_try_status_with_fallback` → absorbed into `_try_update_status`
- `_update_failed_status` → direct call to `_try_update_status`

### Test impact

- `TestTryStatusWithFallback` → rewrite as fallback tests for `_try_update_status`
- `TestUpdateFailedStatus` → remove (covered by `_try_update_status` tests)
- `TestFinalizeRunStatus` → update mocks (no more lambda/`_try_status_with_fallback`)
- `TestTryUpdateStatus` → extend with `conn=None` case

## Notes

Identified during code-simplifier review of ticket 260205-132314.
