---
priority: 3
tags: [enhancement, gui, ux]
description: "GUI: 進捗表示とログ保持の改善"
created_at: "2026-01-29T14:05:04Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# GUI: 進捗表示とログ保持の改善

## 概要

現在のGUIでは処理の進捗がわかりにくく、ページを切り替えるとログが消えてしまう問題がある。

## 問題点

### 1. 進捗表示の不足

- 処理中の進捗率が表示されない
- どのステップを実行中かわかりにくい
- 完了までの目安がわからない

### 2. ログの揮発性

- ページを切り替えるとログ表示がクリアされる
- 現在の状況がわからなくなる
- エラー発生時のデバッグが困難

## 期待される動作

### 進捗表示

- プログレスバーで進捗率を表示（例: 25%, 50%, 75%, 100%）
- 現在のステップを明示（例: "Step 2/5: Generating glossary..."）
- 各ステップの処理時間や残り時間の目安表示

### ログ保持

- ページを切り替えてもログが保持される
- 過去のログを遡って確認できる
- ログのエクスポート機能（オプション）

## 実装案

### 進捗表示

```typescript
interface RunProgress {
  currentStep: number;
  totalSteps: number;
  stepName: string;
  percentComplete: number;
}
```

バックエンドからstep情報を含むログを送信し、フロントエンドで進捗バーを更新する。

### ログ保持

- React Context または Zustand でログ状態を管理
- プロジェクト単位でログを保持
- ログの最大行数を設定可能に

## Tasks

- [ ] 進捗表示の設計
- [ ] バックエンドのstep情報送信を実装
- [ ] フロントエンドの進捗バーを実装
- [ ] ログ状態管理の実装
- [ ] 動作確認

## Notes

- 優先度は低め（機能改善）
- バグ修正後に対応
