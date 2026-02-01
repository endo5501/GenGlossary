---
priority: 1
tags: [bug, frontend, critical]
description: "Files画面でファイル追加ボタンクリック時にファイル選択ダイアログが表示されない"
created_at: "2026-02-01T12:48:09Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# ファイル追加ダイアログが表示されない

## 概要

Files画面でファイルを追加する際、以前は追加ボタンをクリックするとファイル選択ダイアログが
表示されたが、現在は表示されなくなっている。

## 現状の問題

- Files画面の追加ボタンをクリックしても何も起こらない
- ファイル選択ダイアログが開かない
- ファイルの追加ができない状態

## 期待する動作

- 追加ボタンをクリックするとファイル選択ダイアログが表示される
- ファイルを選択して追加できる

## 再現手順

1. アプリケーションを起動
2. Filesメニューを選択
3. ファイル追加ボタンをクリック
4. → ファイル選択ダイアログが表示されない（期待: 表示される）

## Tasks

- [ ] 原因調査（イベントハンドラー、input要素の状態など）
- [ ] 修正実装
- [ ] 手動テストで動作確認
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

- リグレッションバグの可能性が高い
- 最近のコミットで関連する変更がないか確認する
