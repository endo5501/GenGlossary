---
priority: 1
tags: [bug, gui]
description: "GUI: Run完了後もステータスがRunningのまま更新されない"
created_at: "2026-01-29T14:05:04Z"
started_at: 2026-01-29T14:19:28Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# GUI: Run完了後もステータスがRunningのまま更新されない

## 概要

パイプライン実行が完了し、ログに「completed」と表示されているにもかかわらず、UIのステータス表示が「Running」のままになる。

## 再現手順

1. GUIでプロジェクトを作成
2. ドキュメントを登録
3. Runボタンを押して実行
4. ログに「Pipeline execution completed」と表示される
5. しかしUIのステータスは「Running」のまま

## 期待される動作

- パイプライン完了後、UIのステータスが「Completed」または「Idle」に更新される
- Runボタンが再度有効になる

## 調査ポイント

1. **バックエンドのrun状態更新**: RunManagerがrun完了時に状態を正しく更新しているか
2. **フロントエンドのポーリング**: useRunsフックがrun状態の変更を検知しているか
3. **WebSocketまたはSSE**: リアルタイム更新機構が正しく動作しているか

## Tasks

- [x] 原因を調査する
- [x] 修正を実装する
- [x] 動作確認（部分的）

## 原因

調査の結果、以下の2つの問題が特定されました：

### 1. 型定義の不一致（主原因）
- **バックエンド**: `finished_at` フィールドを使用
- **フロントエンド**: `completed_at` フィールドを期待

この不一致により、フロントエンドがバックエンドのレスポンスを正しくパースできていませんでした。

### 2. SSE完了後のキャッシュ無効化がない
- SSEで`complete`イベントを受信後、React Queryのキャッシュが無効化されない
- 最新のrun状態が取得できていない

## 修正内容

1. **型定義の統一**: `completed_at` → `finished_at` に修正、`triggered_by`と`error_message`フィールドを追加
2. **SSE完了時のキャッシュ無効化**: `useLogStream`に`onComplete`コールバックを追加し、AppShellでキャッシュを無効化

修正ファイル:
- `frontend/src/api/types.ts`
- `frontend/src/api/hooks/useLogStream.ts`
- `frontend/src/components/layout/LogPanel.tsx`
- `frontend/src/components/layout/AppShell.tsx`
- `frontend/src/mocks/handlers.ts`
- `frontend/src/__tests__/terms-workflow.test.tsx`

## Notes

- 関連: Issues画面やRefined画面に何も表示されない問題と関連している可能性あり
