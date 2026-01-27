---
priority: 7.5
tags: [frontend, gui, settings]
description: "Implement Settings page UI for project configuration (name, LLM settings)."
created_at: "2026-01-25T00:00:00Z"
started_at: 2026-01-27T13:08:03Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# Ticket Overview

Build the Settings page accessible from the left sidebar. Allow users to modify
project name and LLM configuration (provider, model). Integrate with the project
update API.

Reference: `plan-gui.md` 「Settings（設定）」セクション


## Tasks

- [x] **Red**: テスト追加（`frontend/src/__tests__/settings-page.test.tsx`）
- [x] テスト失敗を確認（Red完了）
- [x] 左サイドバーにSettingsリンク追加
- [x] Settings画面のルーティング設定
- [x] プロジェクト名変更フォーム
  - テキスト入力
  - バリデーション（空文字不可、重複チェック）
- [x] LLM設定フォーム
  - Provider選択（Ollama / OpenAI Compatible）
  - Model入力
  - ベースURL入力（OpenAI Compatible時）
- [x] 保存ボタン実装
  - API呼び出し (PATCH /api/projects/{id})
  - 成功/エラートースト表示
- [x] ローディング状態とエラー状態の表示
- [x] **Green**: テスト通過確認
- [x] Code review by codex MCP
- [x] Code simplification review using code-simplifier agent
- [x] Update docs/architecture/*.md
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing


## Notes

Mantineのフォームコンポーネントを使用。react-hook-formまたはMantine formとの
統合を検討。

Dependencies: Tickets #4 (frontend scaffold), #5 (project views) must be completed first.

## Implementation Summary (2026-01-27)

### Backend Changes
- Added `llm_base_url` field to Project model with default empty string
- DB schema migration v1 → v2 with `llm_base_url` column
- Extended `ProjectUpdateRequest` to support `name` and `llm_base_url` updates
- Added duplicate name check (409 error) on project update

### Frontend Changes
- Installed `@mantine/notifications` for toast notifications
- Created `SettingsPage` component at `/projects/$projectId/settings`
- Form fields: Project Name, Provider (Select), Model (TextInput), Base URL (conditional)
- Base URL field only visible when OpenAI provider is selected
- Save button disabled when no changes detected
- Toast notifications for success/error states
- Updated `LeftNavRail` to support project-scoped navigation (extracts projectId from URL)

### Test Results
- Backend: 674 passed, 0 errors (pyright)
- Frontend: 71 passed
