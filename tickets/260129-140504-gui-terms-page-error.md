---
priority: 1
tags: [bug, gui]
description: "GUI: Terms/Issues/Refined画面でエラーまたは何も表示されない"
created_at: "2026-01-29T14:05:04Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# GUI: Terms/Issues/Refined画面でエラーまたは何も表示されない

## 概要

パイプライン実行完了後、以下の問題が発生する：

1. **Terms画面**: "Something went wrong!", "Cannot read properties of undefined (reading 'length')" エラーが表示される
2. **Issues画面**: 何も表示されない
3. **Refined画面**: 何も表示されない

## 再現手順

1. GUIでプロジェクトを作成し、ドキュメントを登録
2. Runボタンを押して実行
3. ログに「completed」と表示された後、各画面に遷移

## 期待される動作

- Terms画面: 抽出された用語のリストが表示される
- Issues画面: レビューで発見された問題のリストが表示される
- Refined画面: 改善された用語集が表示される

## 調査ポイント

### Terms画面のエラー

```
Cannot read properties of undefined (reading 'length')
```

- APIレスポンスの形式が期待と異なる可能性
- undefinedチェックの不足

### Issues/Refined画面

- データがDBに正しく保存されているか確認
- APIエンドポイントが正しくデータを返しているか確認

## Tasks

- [ ] Terms画面のエラー原因を調査
- [ ] Issues/Refined画面のデータフローを調査
- [ ] 修正を実装
- [ ] 動作確認

## Notes

- Run状態が更新されない問題と関連している可能性あり
