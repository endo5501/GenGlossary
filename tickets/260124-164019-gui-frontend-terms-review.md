---
priority: 8
tags: [frontend, gui, pipeline]
description: "Deliver Terms/Provisional/Issues/Refined views with run controls and log viewer integration."
created_at: "2026-01-24T16:40:19Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# Ticket Overview

Implement the core workflow views after files are ingested: Terms, Provisional, Issues, Refined, and export. Add per-section action buttons (re-run, regenerate, export) and surface run state/logs from the operations API.

Reference: `plan-gui.md` 「Terms」「Provisional」「Issues」「Refined」「グローバル操作バー」「ログビュー」セクション。


## Tasks

- [ ] **Red**: 先にUIテスト追加（`frontend/src/__tests__/terms-workflow.test.tsx`）— Terms/Provisional/Issues/Refined各タブの表示・アクション、実行ボタンの状態制御、ログストリームの表示をRTL+mock SSEで失敗させる
- [ ] テスト失敗を確認（Red完了）
- [ ] Terms view: table with term/category/count/first-doc + detail pane showing occurrences and exclude/edit/manual-add actions
- [ ] Provisional view: table with term/definition/confidence + detail editor with confidence slider and regenerate-this-term
- [ ] Issues view: filterable list by issue_type with detail panel; re-run issues generation button
- [ ] Refined view: list with export to Markdown action; show occurrence list per term
- [ ] Global run controls in header (Full/From-Terms/etc.) wired to operations API; show status badge
- [ ] Log viewer pane consuming SSE/WebSocket stream; show inline progress per run（`docs/architecture.md`にログ/状態連携を追記）
- [ ] **Green**: 追加テストを含めフロントテスト/ビルドが通ることを確認
- [ ] Code simplification review using code-simplifier agent
- [ ] Update docs/architecture/*.md
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing


## Notes

Match layout described in plan-gui.md (upper action bar, mid list+detail). Ensure actions are disabled while run is active to avoid double triggers.
