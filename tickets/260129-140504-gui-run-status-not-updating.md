---
priority: 1
tags: [bug, gui]
description: "GUI: Run完了後もステータスがRunningのまま更新されない"
created_at: "2026-01-29T14:05:04Z"
started_at: null  # Do not modify manually
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

- [ ] 原因を調査する
- [ ] 修正を実装する
- [ ] 動作確認

## Notes

- 関連: Issues画面やRefined画面に何も表示されない問題と関連している可能性あり
