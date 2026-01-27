---
priority: 1
tags: [gui, frontend, routing, critical]
description: "ナビゲーション/ルーティング修正 - 各ページが正しく表示されるよう修正"
created_at: "2026-01-27T16:32:55Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# ナビゲーション/ルーティング修正（最優先・重大）

## 概要

プロジェクトを開いた後、Files/Terms/Provisional/Issues/Refined/Settings をクリックすると「This page will be implemented in a future ticket.」と表示される問題を修正する。

## 症状

- プロジェクトを開いた後でも、各ページで PagePlaceholder が表示される
- 実際のページコンポーネント（FilesPage, TermsPage 等）は実装済み

## 根本原因の可能性

1. LeftNavRail のナビゲーションが `/projects/{id}/files` ではなく `/files` に遷移している
2. ルーティング設定の問題
3. `useLocation()` や `extractProjectId()` の動作不良

## 修正対象ファイル

- `frontend/src/components/layout/LeftNavRail.tsx` - ナビゲーションロジック
- `frontend/src/routes/index.tsx` - ルーティング設定
- `frontend/src/components/layout/AppShell.tsx` - レイアウト

## Tasks

- [ ] LeftNavRailのナビゲーションロジックをデバッグ
- [ ] `/projects/{id}/files` 等のルートが正しく動作することを確認
- [ ] `extractProjectId()` と `getPath()` の動作確認
- [ ] 必要に応じてルーティング設定を修正
- [ ] 全ページ（Files, Terms, Provisional, Issues, Refined, Settings）の表示確認
- [ ] Code simplification review using code-simplifier agent
- [ ] Code review by codex MCP
- [ ] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## Notes

- このチケットが解決しないと他のページの確認ができないため最優先
- 各ページのコンポーネントは既に実装済み（PagePlaceholderではなく実際のページが表示されるべき）
