---
priority: 9
tags: [gui, frontend, files]
description: "Files画面 - Addボタン機能実装"
created_at: "2026-01-28T13:55:03Z"
started_at: 2026-01-28T13:55:31Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# Files画面 - Addボタン機能実装

## 問題の概要

Files画面の「Add」ボタンをクリックしても何も起きない。`onClick` ハンドラが設定されていないため。

## 調査結果

### 既に実装済みの部分
| 項目 | 状態 | ファイル |
|------|------|---------|
| API エンドポイント | 実装済み | `POST /api/projects/{projectId}/files` |
| Mutation フック | 実装済み | `useCreateFile(projectId)` in `api/hooks/useFiles.ts` |
| Mock ハンドラ | 実装済み | `frontend/src/mocks/handlers.ts` |

### 仕様
- Add ボタンクリック時にパス入力ダイアログを表示
- ユーザーがファイルパスを入力して追加
- `useCreateFile` mutation を使用してAPIを呼び出し

## Tasks

- [x] `AddFileDialog` コンポーネントのテスト作成
- [x] `AddFileDialog` コンポーネントの実装（パス入力フォーム）
- [x] FilesPage に Add ボタンの onClick ハンドラを追加
- [x] FilesPage のテスト追加
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent
- [x] Code review by codex MCP
- [x] Update docs/architecture/*.md
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing

## 修正対象ファイル

- `frontend/src/pages/FilesPage.tsx`
- `frontend/src/components/dialogs/AddFileDialog.tsx` (新規作成)
- `frontend/src/__tests__/components/dialogs/AddFileDialog.test.tsx` (新規作成)
- `frontend/src/__tests__/pages/FilesPage.test.tsx` (必要に応じて更新)

## Notes

TDD で進める。まずテストを作成し、失敗を確認してからコミット、その後実装。
