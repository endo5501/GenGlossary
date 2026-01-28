---
priority: 2
tags: [gui, frontend, file-handling]
description: "Files画面のAddボタンをファイル選択ダイアログに改善"
created_at: "2026-01-28T15:51:13Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# Ticket Overview

Files画面のAddボタンの機能を改善する。

## 現状の問題

1. Addボタンを押すとファイルパス入力画面が表示される
2. テキストファイル(txt, md)のパスを入力しても正しく動作しない
3. ユーザーにファイルパスを正確に入力させるのは使いにくいインターフェース

## 改善内容

- Addボタンを押すとOSネイティブのファイル選択ダイアログを表示
- テキストファイル（.txt, .md）のみをフィルタリング
- 複数ファイルを同時に選択可能
- 選択したファイルをプロジェクトに登録

## Tasks

- [ ] 現状のAddボタン実装を調査
- [ ] ファイル選択ダイアログの実装（Electron dialog API使用）
- [ ] テキストファイル（.txt, .md）フィルタの設定
- [ ] 複数ファイル選択の対応
- [ ] 選択したファイルをプロジェクトに登録する処理の実装
- [ ] エラーハンドリング（ファイル読み込み失敗、無効なファイル形式など）
- [ ] テストの作成
- [ ] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [ ] Code simplification review using code-simplifier agent
- [ ] Code review by codex MCP
- [ ] Update docs/architecture/*.md
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing


## Notes

- ElectronのBrowserWindow.showOpenDialog APIを使用してネイティブダイアログを実装
- IPCを通じてRenderer processからMain processのダイアログを呼び出す
- 既存のAddFileDialogコンポーネントは削除または大幅に変更が必要
