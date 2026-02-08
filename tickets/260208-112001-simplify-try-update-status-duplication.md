---
priority: 4
tags: [backend, refactoring]
description: "Simplify _try_update_status duplicated logic and document transaction commit policy"
created_at: "2026-02-08T11:20:01Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# Simplify _try_update_status and document transaction commit policy

## Overview

Code review during the transaction/commit overlap fix (260205-132316) identified two improvement opportunities:

### 1. Extract duplicated logic in _try_update_status

`RunManager._try_update_status()` has duplicated logic between primary and fallback connection paths:

```python
result = update_run_status_if_active(conn, run_id, status, error_message)
conn.commit()
self._log_update_result(run_id, status, result)
return True
```

This pattern appears twice and could be extracted to a helper method.

### 2. Document transaction commit policy

The codebase now follows a clear pattern:
- **Repository layer**: Does NOT commit (data operations only)
- **Manager/Executor layer**: Commits after calling repository functions

This policy should be documented to prevent future confusion.

## Tasks

- [ ] Extract helper method from `_try_update_status` duplicated logic
- [ ] Add docstring/comment documenting commit policy in repository module
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

Identified during code review of ticket 260205-132316-fix-transaction-commit-overlap.
