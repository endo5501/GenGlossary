---
priority: 4
tags: [backend, refactoring]
description: "Refactor RunManager._execute_run into smaller methods"
created_at: "2026-02-07T03:53:07Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# Refactor _execute_run into smaller methods

## Overview

`RunManager._execute_run` は102行あり複数の責任を持つ。セットアップ、パイプライン実行、エラーハンドリングを個別メソッドに分割してテスタビリティと可読性を向上させる。

code-simplifier レビューで指摘（260205-224219-consolidate-runmanager-status-methods チケット対応時）。

## Related Files

- `src/genglossary/runs/manager.py`
- `tests/runs/test_manager.py`

## Tasks

- [ ] Extract setup phase (connection, status update, context creation)
- [ ] Extract pipeline execution phase (executor creation, execution, cleanup)
- [ ] Simplify error handling in _execute_run
- [ ] Update tests if necessary
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

- 現在の _execute_run の責任: DB接続確立、ステータス更新、ログコールバック作成、キャンセルイベント取得、実行コンテキスト作成、エグゼキューター管理、ステータス最終化、外部エラーハンドリング、リソースクリーンアップ
