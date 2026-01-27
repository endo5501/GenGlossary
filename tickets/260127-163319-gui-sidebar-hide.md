---
priority: 4
tags: [gui, frontend, layout]
description: "プロジェクト未選択時のサイドバー非表示"
created_at: "2026-01-27T16:33:19Z"
started_at: null  # Do not modify manually
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

- [ ] AppShellでprojectIdの有無を判定
- [ ] projectIdがない場合はNavbarを非表示
- [ ] ホーム画面でのレイアウト確認
- [ ] Code simplification review using code-simplifier agent
- [ ] Code review by codex MCP
- [ ] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## Notes

- MantineのAppShellはNavbarの表示/非表示を制御可能
