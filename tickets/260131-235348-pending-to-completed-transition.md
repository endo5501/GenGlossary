---
priority: 6
tags: [backend, db, design]
description: "Completion can occur from pending state without started_at"
created_at: "2026-01-31T23:53:48Z"
started_at: 2026-02-02T22:05:38Z # Do not modify manually
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

## Design Decision (2026-02-03)

**決定:** 改善案1を採用 - `complete_run_if_not_cancelled` を `running` 状態のみに制限

**理由:** `pending` → `completed` は論理的にあり得ない。必ず `running` を経由すべき。

### 実装方針

**1. runs_repository.py の変更**

- 新規関数 `update_run_status_if_running` を追加
  - `WHERE status = 'running'` のみをチェック
  - `update_run_status_if_active` と同様のシグネチャ
- `complete_run_if_not_cancelled` を変更
  - `update_run_status_if_running` を使用するように変更
  - docstring を更新

**2. 変更しないもの**

- `cancel_run` - pending からのキャンセルは妥当
- `fail_run_if_not_terminal` - pending からの失敗も妥当

### 状態遷移の制約

| 遷移元 | → completed | → cancelled | → failed |
|--------|-------------|-------------|----------|
| pending | ❌ 不可 | ✅ 可能 | ✅ 可能 |
| running | ✅ 可能 | ✅ 可能 | ✅ 可能 |

### テストケース

- `update_run_status_if_running`: running→completed成功、pending→completed失敗
- `complete_run_if_not_cancelled`: running成功、pending失敗、terminal失敗
