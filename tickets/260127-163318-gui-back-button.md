---
priority: 3
tags: [gui, frontend, navigation]
description: "プロジェクト詳細画面に「戻る」ボタン追加"
created_at: "2026-01-27T16:33:18Z"
started_at: 2026-01-28T12:48:16Z # Do not modify manually
closed_at: 2026-01-28T13:04:31Z # Do not modify manually
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

- [x] GlobalTopBarに「戻る」ボタンまたはホームリンクを追加
- [x] タイトル「GenGlossary」をクリック可能にする（オプション）
- [x] プロジェクト選択時のみ戻るボタンを表示
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent
- [x] Code review by codex MCP
- [x] Update docs/architecture/*.md
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing

## Notes

- ユーザビリティ向上のため、タイトルクリックでもホームに戻れると良い
