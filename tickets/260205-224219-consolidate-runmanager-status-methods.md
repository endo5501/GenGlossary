---
priority: 3
tags: [backend, refactoring]
description: "Consolidate status update methods in RunManager"
created_at: "2026-02-05T22:42:19Z"
started_at: null  # Do not modify manually
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

- [ ] Create unified `_update_status_with_fallback` method
- [ ] Update all callers to use new method
- [ ] Remove obsolete methods (`_try_status_with_fallback`, `_update_failed_status`)
- [ ] Optionally extract `_handle_run_failure` helper
- [ ] Update tests if necessary
- [ ] Commit
- [ ] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest`) before reviwing and pass all tests (No exceptions)
- [ ] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Update docs/architecture/*.md
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## Notes

Identified during code-simplifier review of ticket 260205-132314.
