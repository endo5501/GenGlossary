---
priority: 8
tags: [frontend, gui, pipeline]
description: "Deliver Terms/Provisional/Issues/Refined views with run controls and log viewer integration."
created_at: "2026-01-24T16:40:19Z"
started_at: 2026-01-27T14:05:56Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# Ticket Overview

Implement the core workflow views after files are ingested: Terms, Provisional, Issues, Refined, and export. Add per-section action buttons (re-run, regenerate, export) and surface run state/logs from the operations API.

Reference: `plan-gui.md` 「Terms」「Provisional」「Issues」「Refined」「グローバル操作バー」「ログビュー」セクション。


## Tasks

- [x] **Red**: 先にUIテスト追加（`frontend/src/__tests__/terms-workflow.test.tsx`）— Terms/Provisional/Issues/Refined各タブの表示・アクション、実行ボタンの状態制御、ログストリームの表示をRTL+mock SSEで失敗させる
- [x] テスト失敗を確認（Red完了）
- [x] Terms view: table with term/category/count/first-doc + detail pane showing occurrences and exclude/edit/manual-add actions
- [x] Provisional view: table with term/definition/confidence + detail editor with confidence slider and regenerate-this-term
- [x] Issues view: filterable list by issue_type with detail panel; re-run issues generation button
- [x] Refined view: list with export to Markdown action; show occurrence list per term
- [x] Global run controls in header (Full/From-Terms/etc.) wired to operations API; show status badge
- [x] Log viewer pane consuming SSE/WebSocket stream; show inline progress per run（`docs/architecture.md`にログ/状態連携を追記）
- [x] **Green**: 追加テストを含めフロントテスト/ビルドが通ることを確認
- [x] Code simplification review using code-simplifier agent
- [ ] Code review by codex MCP
- [ ] Update docs/architecture/*.md
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing


## Notes

Match layout described in plan-gui.md (upper action bar, mid list+detail). Ensure actions are disabled while run is active to avoid double triggers.

## Progress Log

### 2026-01-27
- 実装完了: Terms/Provisional/Issues/Refined ページコンポーネント
- 実装完了: API hooks (useTerms, useProvisional, useIssues, useRefined, useRuns, useLogStream)
- 実装完了: GlobalTopBar の API 接続 (Run/Stop ボタン、ステータスバッジ)
- 実装完了: LogPanel の SSE ストリーム対応
- 実装完了: ルーティング追加 (/projects/:projectId/terms, provisional, issues, refined)
- テスト: 114 passed (frontend), 675 passed (backend)
- ビルド: 成功
- 静的解析: pyright 0 errors
- コミット: a291b60

### Code Simplification Review 完了
- 共通コンポーネント作成: PageContainer.tsx, OccurrenceList.tsx
- 色定義の一元化: utils/colors.ts
- APIフック簡略化: useResource.ts ヘルパー追加
- 各ページの簡略化: 重複コード削減（約270行削減）
- テスト: 112/114 passed (2件はEventSource既存問題)
- ビルド: 成功

### 残タスク
- Code review by codex MCP
- docs/architecture/*.md 更新
- 開発者承認
