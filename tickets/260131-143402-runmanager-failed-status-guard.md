---
priority: 1
tags: [refactoring, backend, code-quality]
description: "RunManager: Guard failed status update against terminal states"
created_at: "2026-01-31T14:34:02Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# RunManager: Guard failed status update against terminal states

## 概要

codex MCP レビューで指摘された問題。`_try_failed_status` が既存の終了状態を上書きする可能性がある。

## 問題

- `_try_failed_status` は `update_run_status` を無条件で呼び出す
- 他のスレッド/プロセスが先に cancel/complete を設定した場合、それを上書きする可能性
- cancel/complete の no-op セマンティクスと一貫性がない

## 改善案

1. `update_run_status` に `WHERE status IN ('pending', 'running')` を追加
2. rowcount を返して実際に更新されたか確認
3. `cancel_run`, `complete_run_if_not_cancelled` と同様のパターンを適用

## 関連ファイル

- `src/genglossary/runs/manager.py`
- `src/genglossary/db/runs_repository.py`

## Tasks

- [ ] `update_run_status` を条件付き更新に変更（または新しい関数を作成）
- [ ] `_try_failed_status` で rowcount を確認
- [ ] テストの追加
- [ ] Commit
- [ ] Run static analysis (`pyright`) before reviewing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest`) before reviewing and pass all tests (No exceptions)
- [ ] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Update docs/architecture/*.md
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing
