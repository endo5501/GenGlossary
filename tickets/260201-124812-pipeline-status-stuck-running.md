---
priority: 1
tags: [bug, backend, critical]
description: "Pipeline完了後も状態がRunningのまま更新されない問題"
created_at: "2026-02-01T12:48:12Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# パイプライン状態がRunningのまま

## 概要

ログで「Pipeline execution completed」と表示されても、
パイプラインの状態が「Running」のまま更新されない。

## 現状の問題

- パイプライン処理が完了したログが出力される
- しかし、UI上の状態表示は「Running」のまま
- ユーザーは処理が完了したかどうか判断できない

## 期待する動作

- パイプライン完了時に状態が「Completed」または「Done」に更新される
- UI上でも完了状態が反映される

## 調査ポイント

- パイプライン完了時の状態更新ロジック
- フロントエンドへの状態通知（WebSocket/ポーリング）
- 状態管理の同期

## Tasks

- [ ] バックエンドの状態更新ロジック確認
- [ ] フロントエンドの状態取得/更新ロジック確認
- [ ] 原因特定と修正
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

- 状態遷移: Pending → Running → Completed/Failed
- エラー時は「Failed」状態への遷移も確認する
