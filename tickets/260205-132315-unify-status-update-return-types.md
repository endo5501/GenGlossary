---
priority: 3
tags: [backend, refactoring, api-design]
description: "Unify return types for status update functions in runs_repository"
created_at: "2026-02-05T13:23:15Z"
started_at: null  # Do not modify manually
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

- [ ] Update `update_run_status_if_running` to return `RunUpdateResult`
- [ ] Update `complete_run_if_not_cancelled` to return `RunUpdateResult`
- [ ] Update `fail_run_if_not_terminal` to return `RunUpdateResult`
- [ ] Update all callers in manager.py
- [ ] Update tests
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

This is a medium-sized refactoring. Consider doing this together with the wrapper function removal ticket for efficiency.
