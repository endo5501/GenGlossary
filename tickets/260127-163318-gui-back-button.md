---
priority: 3
tags: [gui, frontend, navigation]
description: "プロジェクト詳細画面に「戻る」ボタン追加"
created_at: "2026-01-27T16:33:18Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# プロジェクト詳細画面に「戻る」ボタン追加

## 概要

プロジェクト詳細画面からホーム（プロジェクト一覧）に戻れるようにする。

## 仕様

各プロジェクト詳細画面には「戻る」ボタンがあり、それを押すとプロジェクト一覧（ホーム）へ戻る。

## 現状の実装

- `GlobalTopBar.tsx` のタイトル「GenGlossary」はクリック不可
- `LeftNavRail.tsx` にホームへのリンクがない
- 「戻る」ボタンがない

## 修正対象ファイル

- `frontend/src/components/layout/GlobalTopBar.tsx`

## Tasks

- [ ] GlobalTopBarに「戻る」ボタンまたはホームリンクを追加
- [ ] タイトル「GenGlossary」をクリック可能にする（オプション）
- [ ] プロジェクト選択時のみ戻るボタンを表示
- [ ] Code simplification review using code-simplifier agent
- [ ] Code review by codex MCP
- [ ] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## Notes

- ユーザビリティ向上のため、タイトルクリックでもホームに戻れると良い
