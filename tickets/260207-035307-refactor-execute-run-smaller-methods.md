---
priority: 3
tags: [backend, refactoring]
description: "Refactor RunManager._execute_run into smaller methods"
created_at: "2026-02-07T03:53:07Z"
started_at: 2026-02-08T12:24:31Z # Do not modify manually
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

- [x] Extract setup phase (connection, status update, context creation)
- [x] Extract pipeline execution phase (executor creation, execution, cleanup)
- [x] Simplify error handling in _execute_run
- [x] Update tests if necessary
- [x] Commit
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Update docs (glob: "*.md" in ./docs/architecture)
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing

## Design

### Approach: 2メソッド抽出

`_execute_run` から2つのプライベートメソッドを抽出し、オーケストレーターとして残す。

### `_setup_run(run_id) -> (conn, context)`

- DB接続の確立
- ステータスを "running" に更新
- ログコールバック作成
- キャンセルイベント取得
- ExecutionContext 作成
- 戻り値: `(sqlite3.Connection, ExecutionContext)`

### `_run_pipeline(conn, run_id, scope, context) -> (error, traceback)`

- Config取得、debug_dir計算
- PipelineExecutor 作成・登録
- パイプライン実行
- executor 参照削除・close
- 戻り値: `(Exception | None, str | None)`

### リファクタリング後の `_execute_run`

- 110行 → 約35行に削減
- 3ステップの流れが一目でわかる: setup → pipeline → finalize
- 外部エラーハンドリング（except）と finally のクリーンアップはそのまま残す
- 挙動変更なし、既存テストで検証

### テスト方針

- 既存テストがすべて通ることを確認（挙動変更なしのリファクタリング）
- 新メソッドの個別テストは追加しない（プライベートメソッド、_execute_run 経由で十分テスト済み）

## Notes

- 現在の _execute_run の責任: DB接続確立、ステータス更新、ログコールバック作成、キャンセルイベント取得、実行コンテキスト作成、エグゼキューター管理、ステータス最終化、外部エラーハンドリング、リソースクリーンアップ
