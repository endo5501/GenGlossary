---
priority: 2
tags: [backend, bug-prevention]
description: "Close PipelineExecutor on completion/failure to prevent resource leak"
created_at: "2026-02-05T23:12:54Z"
started_at: 2026-02-08T10:06:34Z # Do not modify manually
closed_at: 2026-02-08T10:16:44Z # Do not modify manually
---

# Close PipelineExecutor on completion/failure

## Overview

Codex review identified a potential resource leak:

`PipelineExecutor.close()` is only called from `cancel_run`; `_execute_run` never closes the executor on success or non-cancel failure.

## Related Files

- `src/genglossary/runs/manager.py:185-210` (`_execute_run` pipeline execution)
- `src/genglossary/runs/manager.py:267-271` (`cancel_run`)

## Current Behavior

```python
# In _execute_run
try:
    executor.execute(conn, scope, context, doc_root=self.doc_root)
except Exception as e:
    pipeline_error = e
    pipeline_traceback = traceback.format_exc()
finally:
    # Cleanup executor reference only
    with self._executors_lock:
        self._executors.pop(run_id, None)
    # executor.close() is NOT called
```

## Problem

- If `PipelineExecutor` holds sockets/HTTP clients, they may leak until GC
- `close()` is only called in `cancel_run`, not on normal completion or failure
- Resources may accumulate over multiple runs

## Proposed Solution

Call `executor.close()` in the `finally` block:

```python
finally:
    with self._executors_lock:
        self._executors.pop(run_id, None)
    executor.close()  # Always close
```

Or use a context manager if `PipelineExecutor` supports it.

## Tasks

- [x] Review `PipelineExecutor` implementation to confirm `close()` behavior
- [x] Add `executor.close()` call in `_execute_run` finally block
- [x] Consider making `PipelineExecutor` a context manager → YAGNI（使用箇所が1箇所のみ）
- [x] Add test for proper resource cleanup (5 tests added)
- [x] Commit
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Update docs (glob: "*.md" in ./docs/architecture)
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions) → 0 errors
- [x] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions) → 1475 passed
- [x] Get developer approval before closing

## Notes

Identified by codex MCP during review of ticket 260205-224243.

### Review findings addressed
- `executor.close()` exception safety: wrapped in try/except to prevent status masking
- `OpenAICompatibleClient` missing `close()`: created ticket 260208-101337-openai-client-missing-close-method
- Context manager not needed (YAGNI): single usage site, finally block suffices
- Double close (cancel_run + finally): intentional for immediate cancellation, httpx close() is idempotent
