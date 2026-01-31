---
priority: 4
tags: [improvement, backend, threading]
description: "RunManager: Improve start_run in-memory state consistency"
created_at: "2026-01-31T13:47:30Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# RunManager: Improve start_run in-memory state consistency

## 概要

`start_run()` メソッドでは、DB にアクティブな run を作成した後、ロックを解放してからインメモリ状態（`_current_run_id`, `_cancel_events`）を更新している。これにより、DB 状態とインメモリ状態の間に不整合ウィンドウが生じる。

## 現状の問題

### codex MCP レビューからの指摘

**場所**: `src/genglossary/runs/manager.py` (start_run)

1. **High**: `start_run` は `_start_run_lock` を解放した後で `_current_run_id` と `_cancel_events` を更新している。DB でアクティブな run が表示されているが、インメモリ状態がまだ更新されていないウィンドウがある。

2. **Medium**: ロック順序逆転リスク - `start_run` は `_start_run_lock` → `_cancel_events_lock` の順でロックを取得。他のメソッドが逆順でロックを取得するとデッドロックの可能性がある。

3. **Medium**: DB run 作成後、`_cancel_events` が設定される前に例外が発生すると、キャンセルできないアクティブな run が残る可能性がある。

## 影響範囲の分析

- `_current_run_id` は現在クラス内で読み取られていない（未使用）ため、問題は発生しない
- `_cancel_events` の競合ウィンドウは、run 開始直後（スレッド開始前）にキャンセルを試みる極めてまれなケースのみ。その場合キャンセルは単に無視される（192-193 行目の `get` が None を返す）
- ロック順序逆転リスクは現在のコードでは発生しない（`_start_run_lock` は `start_run` でのみ使用）

## 提案する解決策

1. `_current_run_id` の設定と `_cancel_events` への追加を `_start_run_lock` 内で行う
2. または、状態管理用の専用ロックを導入
3. 例外発生時のクリーンアップ処理を追加

## Tasks

- [ ] 設計レビュー・承認
- [ ] 実装
- [ ] テストの更新
- [ ] Commit
- [ ] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [ ] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Update docs/architecture/*.md
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## Notes

- 260130-runmanager-start-run-synchronization チケットの codex MCP レビューで指摘
- 現状は重大な問題ではないが、将来の拡張時に問題になる可能性がある
- 優先度 4 として登録
