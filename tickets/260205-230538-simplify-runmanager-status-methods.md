---
priority: 3
tags: [backend, refactoring]
description: "Simplify RunManager status update methods and rename ALREADY_TERMINAL enum"
created_at: "2026-02-05T23:05:38Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# Simplify RunManager status update methods + Rename ALREADY_TERMINAL enum

## Overview

Code-simplifier review identified opportunities to reduce redundancy in RunManager's status update methods. Additionally, `RunUpdateResult.ALREADY_TERMINAL` needs renaming as it is inaccurate.

## Related Files

- `src/genglossary/runs/manager.py`
- `src/genglossary/db/runs_repository.py`
- `tests/db/test_runs_repository.py`
- `tests/runs/test_manager.py`

## Proposed Changes

### 1. Consolidate status update methods

Merge `_try_status_with_fallback` and `_update_failed_status` into `_try_update_status`:
- Make `_try_update_status` accept `conn: sqlite3.Connection | None`
- Add fallback logic directly into `_try_update_status`
- Remove lambda function wrappers

### 2. Extract error broadcast helper

Create `_broadcast_error` helper to reduce duplication:
```python
def _broadcast_error(
    self,
    run_id: int,
    error_message: str,
    error_traceback: str,
    log_to_logger: bool = True,
) -> None:
```

### 3. Use setdefault for dict operations

Simplify `register_subscriber`:
```python
# Before
if run_id not in self._subscribers:
    self._subscribers[run_id] = set()
self._subscribers[run_id].add(queue)

# After
self._subscribers.setdefault(run_id, set()).add(queue)
```

### 4. Rename ALREADY_TERMINAL enum value

`RunUpdateResult.ALREADY_TERMINAL` は `update_run_status_if_running` で `pending`（非terminal）状態にも返されるため、名前が不正確。`NOT_IN_EXPECTED_STATE` や `PRECONDITION_FAILED` 等へ改名する。

## Tasks

- [ ] Rename `ALREADY_TERMINAL` to a more accurate name (e.g. `NOT_IN_EXPECTED_STATE`)
- [ ] Update all references in production code and tests
- [ ] Refactor `_try_update_status` to include fallback logic
- [ ] Remove `_try_status_with_fallback` method
- [ ] Remove `_update_failed_status` method
- [ ] Create `_broadcast_error` helper
- [ ] Simplify `register_subscriber` with setdefault
- [ ] Update all callers
- [ ] Commit
- [ ] Run static analysis (`pyright`) before reviewing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest`) before reviewing and pass all tests (No exceptions)
- [ ] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Update docs (glob: "*.md" in ./docs/architecture)
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## Notes

- Identified during code-simplifier review of ticket 260205-224243.
- Expected to reduce ~50-60 lines of code.
- Enum rename identified by codex MCP review of ticket 260205-132315.
- 統合元チケット: 260207-032015-rename-already-terminal-enum
