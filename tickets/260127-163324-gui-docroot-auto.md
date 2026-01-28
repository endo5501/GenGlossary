---
priority: 7
tags: [gui, frontend, backend, create]
description: "Create画面 - Document Root 自動化"
created_at: "2026-01-27T16:33:24Z"
started_at: 2026-01-28T13:33:46Z # Do not modify manually
closed_at: 2026-01-28T13:49:20Z # Do not modify manually
---

# Create画面 - Document Root 自動化

## 概要

Document Root入力欄を削除し、バックエンドでプロジェクト作成時に自動生成する。

## 現状の問題

- `CreateProjectDialog.tsx` L71-78 で Document Root をユーザに入力させている
- plan-gui.md の仕様では Document Root の入力は記載なし
- ユーザビリティが悪い

## 仕様

- プロジェクト作成時に `./projects/{project_name}/` を自動生成
- ユーザは Document Root を意識しなくて良い

## 修正対象ファイル

- `frontend/src/components/dialogs/CreateProjectDialog.tsx`
- `src/genglossary/api/routers/projects.py`
- `src/genglossary/api/schemas/project_schemas.py`

## Tasks

- [x] フロントエンドから Document Root 入力欄を削除
- [x] バックエンドでプロジェクト作成時に doc_root を自動生成
- [x] APIスキーマから doc_root を任意フィールドに変更（または削除）
- [x] 自動生成されるパスの確認: `./projects/{project_name}/`
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent
- [x] Code review by codex MCP
- [x] Update docs/architecture/*.md
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing

## Notes

- バックエンドの変更が必要
- 既存プロジェクトとの互換性を考慮
