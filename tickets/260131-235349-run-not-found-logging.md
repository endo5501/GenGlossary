---
priority: 2
tags: [backend, logging, improvement]
description: "No-op logging masks 'run not found' case"
created_at: "2026-01-31T23:53:49Z"
started_at: 2026-02-05T13:08:48Z # Do not modify manually
closed_at: 2026-02-05T13:34:13Z # Do not modify manually
---

# No-op logging masks 'run not found' case

## 概要

`update_run_status_if_active` は以下の2つのケースで0を返す：
1. runが既にterminal状態
2. runが存在しない

`_try_update_status` は常に "already in terminal state" とログ出力するため、runが存在しない場合を隠してしまう。

## 問題点

- デバッグ時に、存在しないrun IDへの操作が "terminal state" として報告される
- 潜在的なバグの発見が困難になる可能性

## 関連ファイル

- `src/genglossary/db/runs_repository.py:175-187`
- `src/genglossary/runs/manager.py:392-401`

## 改善案

1. `update_run_status_if_active` で更新前にrunの存在を確認
2. または、Repository層で "not found" と "terminal state" を区別して返す
3. ログメッセージを "skipped (already terminal or not found)" に変更（最小限の対応）

## Tasks

- [x] Decide on the approach (distinguish cases or update log message)
- [x] Implement the chosen solution
- [x] Add tests for run not found case
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

This is a minor logging improvement. The current behavior is functionally correct but could be more informative for debugging.
