---
priority: 6
tags: [backend, db, design]
description: "Completion can occur from pending state without started_at"
created_at: "2026-01-31T23:53:48Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# Completion can occur from pending state without started_at

## 概要

`update_run_status_if_active` は `pending` または `running` 状態のrunを更新できるため、`complete_run_if_not_cancelled` や `_try_complete_status` が一度も開始されていないrun（`started_at` が null）を `completed` に設定できてしまう。

docstring は "still running" と記載しているが、実際には `pending` 状態からも完了可能。

## 問題点

- `started_at` が null のまま `completed` になる可能性
- docstring と実際の動作の不一致
- ビジネスロジック上、開始されていないrunが完了状態になるのは不適切な可能性

## 関連ファイル

- `src/genglossary/db/runs_repository.py:181-187`
- `src/genglossary/db/runs_repository.py:207-223`
- `src/genglossary/runs/manager.py:439-444`

## 改善案

1. `complete_run_if_not_cancelled` を `running` 状態のみに制限
2. または、`pending` から完了する場合は `started_at` を自動設定
3. docstring を実際の動作に合わせて更新

## Tasks

- [ ] Decide on the correct behavior (restrict to running or allow pending)
- [ ] Update implementation based on decision
- [ ] Update docstrings to match behavior
- [ ] Add tests for edge cases
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

This is a design decision that existed before the refactoring. The refactoring preserved the existing behavior.
