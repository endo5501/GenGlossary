---
priority: 6
tags: [gui, frontend, create]
description: "Create画面 - OpenAI設定フィールド追加"
created_at: "2026-01-27T16:33:24Z"
started_at: 2026-01-28T13:23:07Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# Create画面 - OpenAI設定フィールド追加

## 概要

Create画面でprovider=openaiを選択した時に、base_url入力欄を条件付きで表示する。

## 現状の問題

- Create画面では OpenAI を選択しても追加設定フィールドが表示されない
- SettingsPage では条件付き表示で実装済み（L185-193）

## 仕様

- LLM Provider で openai を選択した場合、Base URL 入力欄を表示
- SettingsPage.tsx の実装を参考にする

## 修正対象ファイル

- `frontend/src/components/dialogs/CreateProjectDialog.tsx`

## Tasks

- [x] provider === 'openai' の条件判定を追加
- [x] Base URL 入力フィールドを条件付きで表示
- [x] SettingsPage.tsx の実装を参考にする
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent
- [x] Code review by codex MCP
- [x] Update docs/architecture/*.md
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing

## Notes

- SettingsPage.tsx の実装例：
```tsx
{provider === 'openai' && (
  <TextInput
    label="Base URL"
    placeholder="https://api.openai.com/v1"
    value={baseUrl}
    onChange={(e) => setBaseUrl(e.currentTarget.value)}
    description="Custom API endpoint for OpenAI-compatible providers"
  />
)}
```
