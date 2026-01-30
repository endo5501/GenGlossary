---
priority: 4
tags: [improvement, backend, refactoring]
description: "RunManager: _execute_run method refactoring and hardening"
created_at: "2026-01-30T23:55:00+09:00"
started_at: null
closed_at: null
---

# RunManager: _execute_run method refactoring and hardening

## 概要

`_execute_run` メソッドのコード簡素化とエラーハンドリングの強化。

## code-simplifier レビューからの指摘

### 1. コード重複（高優先度）

**場所**: `src/genglossary/runs/manager.py:148-170`

例外処理ブロックにおいて、ステータス更新ロジックが `conn` と `fallback_conn` で完全に重複している。

**提案**: ヘルパーメソッド `_update_failed_status` に抽出

### 2. ネストの深さ（中優先度）

メインの処理フロー（try ブロック）が複数のネストレベルを含み、認知的複雑度が高い。

**提案**: 初期化・完了処理を別メソッドに分割

### 3. コメント言語混在（低優先度）

日本語と英語のコメントが混在している。

## codex MCP レビューからの指摘

### 1. conn が使用不能な場合の処理（Medium）

**場所**: `src/genglossary/runs/manager.py:151`

`conn` が存在するが使用不能な場合（壊れたトランザクション、"database is locked" など）、except パスで同じ `conn` を使用して再度例外が発生し、ステータス更新とエラーログのブロードキャストが失敗する可能性がある。

**提案**: ネストされた try/except または、`update_run_status` が失敗した場合に新しい接続にフォールバック

### 2. fallback 接続のエラーハンドリング（Medium）

**場所**: `src/genglossary/runs/manager.py:160`

fallback の `database_connection` がガードされていない。失敗すると元の例外がマスクされ、`_broadcast_log` がスキップされ、run ステータスが変更されない。

**提案**: fallback 更新を独自の try/except でラップし、エラーログは必ず出力

### 3. 潜在的な接続リーク（Low）

**場所**: `src/genglossary/runs/manager.py:101`

`get_connection` が接続を開いた後、戻る前に例外を発生させた場合（例：PRAGMA 失敗）、`conn` は `None` のままで開かれた接続がクローズされない。

## 影響範囲

- `src/genglossary/runs/manager.py`

## Tasks

- [ ] ステータス更新ロジックをヘルパーメソッドに抽出
- [ ] conn使用不能時のフォールバック処理追加
- [ ] fallback接続のエラーハンドリング追加
- [ ] テストの更新
- [ ] Commit
- [ ] Run static analysis (`pyright`) and pass all tests
- [ ] Run tests (`uv run pytest`) and pass all tests
- [ ] Code review
- [ ] Get developer approval before closing
