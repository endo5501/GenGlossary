---
priority: 7.5
tags: [frontend, gui, settings]
description: "Implement Settings page UI for project configuration (name, LLM settings)."
created_at: "2026-01-25T00:00:00Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# Ticket Overview

Build the Settings page accessible from the left sidebar. Allow users to modify
project name and LLM configuration (provider, model). Integrate with the project
update API.

Reference: `plan-gui.md` 「Settings（設定）」セクション


## Tasks

- [ ] **Red**: テスト追加（`frontend/src/__tests__/settings-page.test.tsx`）
- [ ] テスト失敗を確認（Red完了）
- [ ] 左サイドバーにSettingsリンク追加
- [ ] Settings画面のルーティング設定
- [ ] プロジェクト名変更フォーム
  - テキスト入力
  - バリデーション（空文字不可、重複チェック）
- [ ] LLM設定フォーム
  - Provider選択（Ollama / OpenAI Compatible）
  - Model入力
  - ベースURL入力（OpenAI Compatible時）
- [ ] 保存ボタン実装
  - API呼び出し (PATCH /api/projects/{id})
  - 成功/エラートースト表示
- [ ] ローディング状態とエラー状態の表示
- [ ] **Green**: テスト通過確認
- [ ] Code simplification review using code-simplifier agent
- [ ] Update docs/architecture/*.md
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing


## Notes

Mantineのフォームコンポーネントを使用。react-hook-formまたはMantine formとの
統合を検討。

Dependencies: Tickets #4 (frontend scaffold), #5 (project views) must be completed first.
