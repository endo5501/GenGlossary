---
priority: 2
tags: [gui, frontend, file-handling]
description: "Files画面のAddボタンをファイル選択ダイアログに改善"
created_at: "2026-01-28T15:51:13Z"
started_at: 2026-01-28T15:53:25Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# Ticket Overview

Files画面のAddボタンの機能を改善する。

## 現状の問題

1. Addボタンを押すとファイルパス入力画面が表示される
2. テキストファイル(txt, md)のパスを入力しても正しく動作しない
3. ユーザーにファイルパスを正確に入力させるのは使いにくいインターフェース

## 改善内容

- Addボタンを押すとファイル選択ダイアログを表示（HTML5 File API + Mantine Dropzone）
- テキストファイル（.txt, .md）のみをフィルタリング
- 複数ファイルを同時に選択可能
- 選択したファイルの内容をDBに保存し、プロジェクトに登録
- ファイルシステムへの依存を排除（ファイル内容をDBに直接保存）

## Tasks

### Phase 1: バックエンド - DBスキーマ変更
- [x] documentsテーブルにcontentカラム追加のテスト作成
- [x] file_path → file_name への変更
- [x] schema.py の実装とマイグレーション

### Phase 2: バックエンド - document_repository変更
- [x] content対応のCRUD関数テスト作成
- [x] document_repository.py の実装

### Phase 3: バックエンド - APIスキーマ変更
- [x] file_schemas.py のリクエスト/レスポンススキーマ変更

### Phase 4: バックエンド - APIエンドポイント変更
- [x] 新APIのテスト作成
- [x] files.py の実装（単一/バルク作成）

### Phase 5: バックエンド - PipelineExecutor変更
- [x] DBからcontentを取得するテスト作成
- [x] executor.py の実装

### Phase 6-8: フロントエンド
- [x] @mantine/dropzone パッケージ追加
- [x] types.ts の型定義変更
- [x] useFiles.ts の複数ファイル一括作成hook追加
- [x] AddFileDialog.tsx をDropzone UIに書き換え
- [x] フロントエンドテスト更新

### 品質保証
- [x] Run static analysis (`pyright`) before reviewing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before reviewing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent
- [x] Code review by codex MCP
- [x] Update docs/architecture/*.md
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing


## Notes

- HTML5 File APIとMantine Dropzoneを使用してファイル選択UIを実装
- FileReader APIでファイル内容を読み取り、バックエンドに送信
- DBスキーマを変更し、documentsテーブルにcontentカラムを追加
- PipelineExecutorはDBから直接ファイル内容を取得（ファイルシステム再読み込み不要）
- diff-scan機能はGUIからは使用不可（ファイルシステムにアクセスできないため）
