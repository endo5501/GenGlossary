---
priority: 4
tags: [gui, frontend, layout]
description: "プロジェクト未選択時のサイドバー非表示"
created_at: "2026-01-27T16:33:19Z"
started_at: 2026-01-28T13:06:01Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# プロジェクト未選択時のサイドバー非表示

## 概要

ホーム画面（projectIdなし）ではLeftNavRailを非表示にする。

## 現状の問題

- ホーム画面でもサイドバー（Files, Terms等のナビゲーション）が表示されている
- プロジェクトが選択されていない状態でナビゲーションをクリックするとPagePlaceholderが表示される

## 修正対象ファイル

- `frontend/src/components/layout/AppShell.tsx`

## Tasks

- [x] AppShellでprojectIdの有無を判定
- [x] projectIdがない場合はNavbarを非表示
- [x] ホーム画面でのレイアウト確認
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent (既に実装済み - 変更不要)
- [x] Code review by codex MCP (既に実装済み - 変更不要)
- [x] Update docs/architecture/*.md (既に実装済み - 変更不要)
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing

## Notes

- MantineのAppShellはNavbarの表示/非表示を制御可能
