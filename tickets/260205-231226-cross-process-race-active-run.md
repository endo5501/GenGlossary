---
priority: 4
tags: [backend, bug-prevention]
description: "Fix cross-process race condition for active run check"
created_at: "2026-02-05T23:12:26Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# Fix cross-process race condition for active run check

## Overview

Codex review identified a cross-process race condition in `start_run`:

Two processes can both see "no active run" and insert a new run, resulting in multiple active runs.

## Related Files

- `src/genglossary/runs/manager.py:86-95` (`start_run`)

## Current Behavior

```python
with self._start_run_lock:  # In-process lock only
    with database_connection(self.db_path) as conn:
        active_run = get_active_run(conn)
        if active_run is not None:
            raise RuntimeError(...)

        with transaction(conn):
            run_id = create_run(conn, ...)
```

## Problem

- `_start_run_lock` only protects against concurrent calls within the same process
- Two separate processes can both pass the `get_active_run` check
- Both processes create a new run, violating the "one active run" constraint

## Proposed Solutions

### Option A: DB-level uniqueness constraint
- Add partial unique index on active status
- Handle `IntegrityError` when constraint is violated

### Option B: Immediate write lock
- Wrap check and create in a single transaction with `BEGIN IMMEDIATE`
- Forces DB-level serialization

### Option C: Guard table/lock row
- Create a separate lock row in a guard table
- Use SELECT FOR UPDATE pattern

## Tasks

- [ ] Choose solution approach
- [ ] Implement DB-level protection
- [ ] Add tests for cross-process scenario (or document why not feasible)
- [ ] Commit
- [ ] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest`) before reviwing and pass all tests (No exceptions)
- [ ] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Update docs (glob: "*.md" in ./docs/architecture)
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## Notes

Identified by codex MCP during review of ticket 260205-224243.
Low risk in current usage (single process), but important for future scalability.
