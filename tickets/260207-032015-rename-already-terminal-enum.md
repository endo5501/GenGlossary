---
priority: 4
tags: [backend, refactoring]
description: "Rename ALREADY_TERMINAL to NOT_IN_EXPECTED_STATE"
created_at: "2026-02-07T03:20:15Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# Rename RunUpdateResult.ALREADY_TERMINAL to NOT_IN_EXPECTED_STATE

## Overview

`RunUpdateResult.ALREADY_TERMINAL` は `update_run_status_if_running` で `pending`（非terminal）状態にも返されるため、名前が不正確。`NOT_IN_EXPECTED_STATE` や `PRECONDITION_FAILED` 等への改名を検討。

codex MCP レビューで指摘（260205-132315-unify-status-update-return-types チケット対応時）。

## Related Files

- `src/genglossary/db/runs_repository.py`
- `src/genglossary/runs/manager.py`
- `tests/db/test_runs_repository.py`
- `tests/runs/test_manager.py`

## Tasks

- [ ] Rename `ALREADY_TERMINAL` to a more accurate name
- [ ] Update all references in production code
- [ ] Update all references in tests
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

- 影響範囲が広い（enum値を参照する全箇所）ため、一括変更が必要
