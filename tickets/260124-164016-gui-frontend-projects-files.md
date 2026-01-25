---
priority: 7
tags: [frontend, gui, projects]
description: "Implement GUI screens for project home, creation dialog, and Files/Document Viewer sections."
created_at: "2026-01-24T16:40:16Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# Ticket Overview

Build the first user-facing screens: project list/home with summary cards, project creation/duplication, and the Files panel plus Document Viewer layout. Wire them to the new APIs and provide sensible loading/error states.

Reference: `plan-gui.md` 「プロジェクト一覧（ホーム）」「Files」「Document Viewer」セクション。


## Tasks

- [ ] **Red**: 先にUIテスト追加（`frontend/src/__tests__/projects-page.test.tsx`）— プロジェクト一覧の表示/選択、作成モーダルのバリデーション、API呼び出しモック、空状態表示、ファイルタブ表示をRTLで失敗させる
- [ ] テスト失敗を確認（Red完了）
- [ ] Home screen: project list with stats (last updated, docs count, issues count) and selection to show right-side summary card（`docs/architecture.md`のUIフローに反映）
- [ ] Implement project create/duplicate/delete dialogs calling API; refresh list and toast results
- [ ] Project detail shell with left nav highlighting and breadcrumbs from global layout
- [ ] Files tab: list documents with status + updated_at; actions to add/replace files and trigger diff scan
- [ ] Document Viewer: tabbed doc selection and right-side term card placeholder; support jump-in from Files row
- [ ] Add optimistic states/spinners and empty states for no projects/no files
- [ ] **Green**: 追加テストを含めフロントテスト/ビルドが通ることを確認
- [ ] Code simplification review using code-simplifier agent
- [ ] Update docs/architecture.md
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing


## Notes

Coordinate file upload UX with backend expectations (path vs. content). Keep navigation consistent with planned sidebar sections.
