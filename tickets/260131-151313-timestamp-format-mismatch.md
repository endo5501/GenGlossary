---
priority: 1
tags: [backend, db, bug]
description: "Timestamp format/timezone mismatch in runs repository"
created_at: "2026-01-31T15:13:13Z"
started_at: 2026-02-01T00:03:41Z # Do not modify manually
closed_at: 2026-02-01T00:16:23Z # Do not modify manually
---

# Timestamp format/timezone mismatch in runs repository

## 概要

`update_run_status_if_active` は SQLite の `datetime('now')` (UTC, `"YYYY-MM-DD HH:MM:SS"` 形式) を使用しているが、`update_run_status` は `datetime.now().isoformat()` (ローカル時間, ISO形式) を使用している。

これにより：
- フォーマットの不一致（ISO vs SQLite形式）
- タイムゾーンの不一致（ローカル vs UTC）

## 関連ファイル

- `src/genglossary/db/runs_repository.py:181-185`
- `src/genglossary/runs/manager.py:112-115`

## 改善案

1. すべてのタイムスタンプを UTC ISO 形式に統一
2. `datetime.now(timezone.utc).isoformat()` を使用

## Tasks

- [x] Investigate current timestamp usage across the codebase
- [x] Decide on unified timestamp format (UTC ISO recommended)
- [x] Update update_run_status_if_active to use Python datetime
- [x] Update update_run_status if needed
- [x] Add tests for timestamp format consistency
- [x] Commit
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Update docs/architecture/*.md
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing

## Notes

This issue existed before the refactoring. The refactoring preserved the existing behavior of `cancel_run`, `complete_run_if_not_cancelled`, and `fail_run_if_not_terminal` which all used `datetime('now')`.
