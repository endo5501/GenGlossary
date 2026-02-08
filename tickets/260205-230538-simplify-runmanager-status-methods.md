---
priority: 3
tags: [backend, refactoring]
description: "Simplify RunManager status update methods and rename ALREADY_TERMINAL enum"
created_at: "2026-02-05T23:05:38Z"
started_at: 2026-02-08T11:27:02Z # Do not modify manually
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

### 1. Rename ALREADY_TERMINAL enum value → NOT_IN_EXPECTED_STATE

`RunUpdateResult.ALREADY_TERMINAL` は `update_run_status_if_running` で `pending`（非terminal）状態にも返されるため、名前が不正確。`NOT_IN_EXPECTED_STATE` へ改名する。

対象ファイル:
- `src/genglossary/db/runs_repository.py`: enum定義、docstring、戻り値コメント
- `src/genglossary/runs/manager.py`: `_log_update_result` での比較、ログメッセージ
- `tests/db/test_runs_repository.py`: テストでの参照
- `tests/runs/test_manager.py`: テストでの参照

### 2. Simplify register_subscriber with setdefault

```python
# Before
if run_id not in self._subscribers:
    self._subscribers[run_id] = set()
self._subscribers[run_id].add(queue)

# After
self._subscribers.setdefault(run_id, set()).add(queue)
```

### Previously completed (no longer needed)

- ~~Consolidate status update methods~~ → `_try_update_status` に統合済み
- ~~Extract error broadcast helper~~ → 不要（統合済み）

## Tasks

- [x] Rename `ALREADY_TERMINAL` to `NOT_IN_EXPECTED_STATE` in enum definition and all docstrings
- [x] Update all references in production code
- [x] Update all references in tests
- [x] Update log message in `_log_update_result`
- [x] Simplify `register_subscriber` with setdefault
- [x] Commit
- [x] Run static analysis (`pyright`) before reviewing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest`) before reviewing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Update docs (glob: "*.md" in ./docs/architecture)
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing

## Notes

- Identified during code-simplifier review of ticket 260205-224243.
- Expected to reduce ~50-60 lines of code.
- Enum rename identified by codex MCP review of ticket 260205-132315.
- 統合元チケット: 260207-032015-rename-already-terminal-enum
