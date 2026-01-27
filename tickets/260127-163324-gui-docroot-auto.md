---
priority: 7
tags: [gui, frontend, backend, create]
description: "Create画面 - Document Root 自動化"
created_at: "2026-01-27T16:33:24Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
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

- [ ] フロントエンドから Document Root 入力欄を削除
- [ ] バックエンドでプロジェクト作成時に doc_root を自動生成
- [ ] APIスキーマから doc_root を任意フィールドに変更（または削除）
- [ ] 自動生成されるパスの確認: `./projects/{project_name}/`
- [ ] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [ ] Code simplification review using code-simplifier agent
- [ ] Code review by codex MCP
- [ ] Update docs/architecture/*.md
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## Notes

- バックエンドの変更が必要
- 既存プロジェクトとの互換性を考慮
