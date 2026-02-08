---
priority: 4
tags: [backend, refactoring]
description: "Simplify _try_update_status and _log_update_result in RunManager"
created_at: "2026-02-08T11:39:11Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# Simplify _try_update_status and _log_update_result in RunManager

## Overview

Code review identified simplification opportunities in RunManager's status update methods and runs_repository's SQL construction.

## Related Files

- `src/genglossary/runs/manager.py` (`_try_update_status`, `_log_update_result`, `_finalize_run_status`)
- `src/genglossary/db/runs_repository.py` (`_update_run_status_if_in_states`)

## Proposed Changes

### 1. Extract `_update_with_connection` helper from `_try_update_status`

Eliminate duplicated update/commit/log pattern by extracting a helper method.

### 2. Use dict mapping in `_log_update_result`

Replace if/elif chain with a dictionary mapping for no-op messages.

### 3. Use guard clauses in `_finalize_run_status`

Reduce nesting by using early returns for cancellation and failure cases.

### 4. Dynamically build SQL in `_update_run_status_if_in_states`

Eliminate SQL duplication by dynamically building UPDATE clause (consistent with `update_run_status` pattern).

## Tasks

- [ ] Extract `_update_with_connection` helper
- [ ] Replace if/elif with dict mapping in `_log_update_result`
- [ ] Apply guard clauses to `_finalize_run_status`
- [ ] Dynamically build SQL in `_update_run_status_if_in_states`
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

- Identified during code-simplifier and codex review of ticket 260205-230538.
