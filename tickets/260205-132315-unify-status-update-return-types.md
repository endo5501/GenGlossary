---
priority: 3
tags: [backend, refactoring, api-design]
description: "Unify return types for status update functions in runs_repository"
created_at: "2026-02-05T13:23:15Z"
started_at: 2026-02-07T03:10:29Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# Unify return types for status update functions in runs_repository

## Overview

The status update functions in `runs_repository.py` have inconsistent return types:

| Function | Return Type |
|----------|-------------|
| `update_run_status_if_active` | `RunUpdateResult` |
| `cancel_run` | `RunUpdateResult` |
| `update_run_status_if_running` | `int` (rowcount) |
| `complete_run_if_not_cancelled` | `bool` |
| `fail_run_if_not_terminal` | `bool` |

This inconsistency can lead to confusion and misuse.

## Related Files

- `src/genglossary/db/runs_repository.py`

## Proposed Change

Standardize all conditional status update functions to return `RunUpdateResult`:

1. `update_run_status_if_running` → return `RunUpdateResult`
2. `complete_run_if_not_cancelled` → return `RunUpdateResult`
3. `fail_run_if_not_terminal` → return `RunUpdateResult`

## Benefits

- Consistent API design
- Better error reporting (distinguish NOT_FOUND from ALREADY_TERMINAL)
- Easier maintenance

## Considerations

- This is a breaking change for callers
- Need to update all call sites
- Tests will need significant updates

## Tasks

- [x] Update `update_run_status_if_running` to return `RunUpdateResult`
- [x] Update `complete_run_if_not_cancelled` to return `RunUpdateResult`
- [x] Update `fail_run_if_not_terminal` to return `RunUpdateResult`
- [x] Update all callers in manager.py (no changes needed - uses update_run_status_if_active directly)
- [x] Update tests
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

### runs_repository.py changes

1. **`_update_run_status_if_in_states`** (internal helper)
   - Return type: `int` → `RunUpdateResult`
   - If rowcount > 0: return `UPDATED`
   - If rowcount == 0: check existence → `NOT_FOUND` or `ALREADY_TERMINAL`
   - Consolidate existence-check logic currently in `update_run_status_if_active`

2. **`update_run_status_if_active`** → pass through `_update_run_status_if_in_states` result directly (remove duplicate existence check)

3. **`update_run_status_if_running`** → return type `int` → `RunUpdateResult`

4. **`complete_run_if_not_cancelled`** → return type `bool` → `RunUpdateResult`

5. **`fail_run_if_not_terminal`** → return type `bool` → `RunUpdateResult`

### Caller changes

- manager.py production code: **No changes needed** (uses `update_run_status_if_active` directly)
- test_manager.py: Update `complete_run_if_not_cancelled` usage (L1342, L1365)
- test_runs_repository.py: Update all test assertions for changed return types

## Notes

This is a medium-sized refactoring. Consider doing this together with the wrapper function removal ticket for efficiency.
