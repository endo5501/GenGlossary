---
priority: 6
tags: [backend, validation]
description: "runs_repository: Add status validation and error_message clearing"
created_at: "2026-02-01T00:28:46Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# runs_repository: Add status validation and error_message clearing

## 概要

runs_repository.py に status 値のバリデーションを追加し、状態遷移時の error_message クリア処理を実装する。

## 問題点

### 1. status のバリデーションがない

`update_run_status` と `update_run_status_if_active` は任意の status 文字列を受け入れる。
タイポや不正な値が渡されると、`get_active_run` や terminal-state ロジックが破綻する。

**改善案:**
```python
VALID_STATUSES = {"pending", "running", "completed", "failed", "cancelled"}
TERMINAL_STATUSES = {"completed", "failed", "cancelled"}

def _validate_status(status: str, allowed: set[str] | None = None) -> None:
    allowed = allowed or VALID_STATUSES
    if status not in allowed:
        raise ValueError(f"Invalid status: {status}. Must be one of {allowed}")
```

### 2. error_message がクリアされない

状態遷移（failed → running → completed など）で明示的にクリアしないと、古いエラーメッセージが残る。

**改善案:**
- `update_run_status` で status が非 terminal になった場合、error_message を NULL にクリアするオプションを追加
- または、呼び出し側で明示的にクリアすることをドキュメント化

## Tasks

- [ ] Add VALID_STATUSES and TERMINAL_STATUSES constants
- [ ] Add _validate_status helper function
- [ ] Add status validation to update_run_status
- [ ] Add status validation to update_run_status_if_active (terminal only)
- [ ] Consider error_message clearing strategy
- [ ] Add tests
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

- Source: Codex MCP review from ticket 260201-001229-additional-timestamp-improvements
