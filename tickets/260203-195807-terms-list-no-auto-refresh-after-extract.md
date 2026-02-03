---
priority: 3
tags: [bug, frontend, ux]
description: "Extract操作後に用語一覧が自動更新されない"
created_at: "2026-02-03T19:58:07Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# Extract操作後に用語一覧が自動更新されない

## 概要

Extract（用語抽出）などの操作を行った後、用語一覧画面が自動的に更新されない。画面を手動でリロードしないと抽出結果が表示されないため、ユーザー体験が損なわれている。

## 期待される動作

1. Extract操作が完了したら、用語一覧が自動的に更新される
2. 他の操作（用語の追加・削除・除外など）後も一覧が自動更新される
3. ユーザーが手動でリロードする必要がない

## 現在の動作

- Extract操作が完了しても一覧が更新されない
- ブラウザをリロードしないと結果が表示されない

## 関連コード

- フロントエンド: Terms画面のデータ取得ロジック
- React Query または状態管理のinvalidation/refetch処理
- SSE/WebSocket経由の完了通知とデータ再取得の連携

## Tasks

- [ ] 問題の原因を調査（React Queryのinvalidation漏れ、SSEハンドリング等）
- [ ] Extract完了時のデータ再取得処理を実装
- [ ] 他の操作（追加・削除・除外）でも同様の問題がないか確認
- [ ] テストの追加
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

- Run完了時のSSEイベントを受け取った後、React Queryのキャッシュをinvalidateする必要がある可能性
- `queryClient.invalidateQueries` の呼び出しが適切に行われているか確認
