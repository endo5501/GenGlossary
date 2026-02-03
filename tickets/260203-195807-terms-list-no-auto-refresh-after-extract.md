---
priority: 3
tags: [bug, frontend, ux]
description: "Extract操作後に用語一覧が自動更新されない"
created_at: "2026-02-03T19:58:07Z"
started_at: 2026-02-03T22:18:37Z # Do not modify manually
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

- [x] 問題の原因を調査（React Queryのinvalidation漏れ、SSEハンドリング等）
- [x] Extract完了時のデータ再取得処理を実装
- [x] 他の操作（追加・削除・除外）でも同様の問題がないか確認
- [x] テストの追加
- [x] Commit
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Update docs/architecture/*.md
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing


## Notes

- Run完了時のSSEイベントを受け取った後、React Queryのキャッシュをinvalidateする必要がある可能性
- `queryClient.invalidateQueries` の呼び出しが適切に行われているか確認

## 解決方法

**根本原因**: SSE 'complete' イベント後に `termKeys.list` がinvalidateされていなかった

**修正内容**:
1. `AppShell.tsx`の`handleRunComplete`で、Run完了時にすべてのデータリストをinvalidate
2. `issueKeys.lists()` → `issueKeys.list(projectId)` に修正（特定プロジェクトのみ無効化）
3. 早期リターンパターンで可読性向上

**コードレビューで見つかった追加課題**:
- エッジケース: ナビゲーション中にSSE完了イベントが発火すると間違ったプロジェクトのキャッシュが無効化される可能性
- 別チケットとして登録: `260203-222752-handlerunomplete-projectid-from-sse-context`

**コミット**:
- `ef06546`: Fix auto-refresh of data lists after run completion
- `2c2b0dd`: Refactor handleRunComplete with early return and fix issueKeys
- `e3f56c3`: Add ticket: handleRunComplete should receive projectId from SSE context
- `17a6be1`: Update frontend.md: document cache invalidation on run completion
