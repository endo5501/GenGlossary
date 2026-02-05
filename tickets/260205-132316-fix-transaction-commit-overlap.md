---
priority: 4
tags: [backend, database, potential-bug]
description: "Fix transaction/commit overlap in update_run_status_if_active"
created_at: "2026-02-05T13:23:16Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
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

## Current Behavior

```python
# manager.py
def _try_update_status(...):
    try:
        with transaction(conn):  # <-- Outer transaction
            result = update_run_status_if_active(...)  # <-- Contains conn.commit()
        ...

# runs_repository.py
def update_run_status_if_active(...):
    ...
    if rowcount > 0:
        conn.commit()  # <-- Inner commit
    ...
```

## Proposed Solutions

**Option A: Remove commit from repository functions**
- Let callers manage transactions
- More explicit but requires caller awareness

**Option B: Add commit flag parameter**
- `update_run_status_if_active(..., auto_commit=True)`
- Backwards compatible but adds complexity

**Option C: Don't wrap in transaction() in manager**
- Rely on repository's internal commit
- Simpler but less consistent

## Current Risk Assessment

- SQLite handles duplicate commits gracefully (no-op)
- All tests pass currently
- Risk is low but design is fragile

## Tasks

- [ ] Analyze which solution is best for the codebase
- [ ] Implement chosen solution
- [ ] Add tests for nested transaction scenarios
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

This issue was identified during code review by Codex. Currently functional but architecturally fragile.
