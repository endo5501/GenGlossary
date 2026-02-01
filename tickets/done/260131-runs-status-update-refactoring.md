---
priority: 2
tags: [refactoring, backend, code-quality]
description: "Refactor runs status update functions to eliminate duplication"
created_at: "2026-01-31T15:00:00Z"
started_at: 2026-01-31T15:00:32Z
closed_at: 2026-02-01T00:02:51Z
---

# Refactor runs status update functions to eliminate duplication

## 概要

code-simplifier レビューで指摘された重複パターンの改善。

## 問題

### Repository層の重複
`cancel_run`, `complete_run_if_not_cancelled`, `fail_run_if_not_terminal` が同じSQL更新パターンを繰り返している。

### Manager層の重複
`_try_cancel_status`, `_try_complete_status`, `_try_failed_status` が同じエラーハンドリング・ログ出力パターンを繰り返している。

## 改善案

### Repository層
汎用的な `update_run_status_if_active` 関数を作成し、既存の関数を薄いラッパーにする。

### Manager層
汎用的な `_try_update_status` メソッドを作成し、3つの専用メソッドを薄いラッパーに変更。

## 関連ファイル

- `src/genglossary/db/runs_repository.py`
- `src/genglossary/runs/manager.py`

## Tasks

- [x] Repository層: `update_run_status_if_active` 関数を作成
- [x] Repository層: 既存3関数を薄いラッパーに変更
- [x] Manager層: `_try_update_status` メソッドを作成
- [x] Manager層: 既存3メソッドを薄いラッパーに変更
- [x] テスト更新
- [x] Commit
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Update docs/architecture/*.md
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing
