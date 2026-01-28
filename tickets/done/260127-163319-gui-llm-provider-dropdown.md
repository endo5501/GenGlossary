---
priority: 5
tags: [gui, frontend, create]
description: "Create画面 - LLM Provider ドロップダウン化"
created_at: "2026-01-27T16:33:19Z"
started_at: 2026-01-28T13:09:39Z # Do not modify manually
closed_at: 2026-01-28T13:21:56Z # Do not modify manually
---

# Create画面 - LLM Provider ドロップダウン化

## 概要

Create画面のLLM ProviderをTextInputからSelectコンポーネントに変更する。

## 現状の問題

- `CreateProjectDialog.tsx` L80-85 で TextInput を使用
- ユーザがフリーテキストで入力（ollama, openai など）
- 入力ミスの可能性がある

## 仕様

- SettingsPage では Select コンポーネントを使用済み
- ドロップダウンメニューで ollama / openai を選択可能にする

## 修正対象ファイル

- `frontend/src/components/dialogs/CreateProjectDialog.tsx`

## Tasks

- [x] TextInput を Select コンポーネントに変更
- [x] 選択肢: ollama, openai
- [x] SettingsPage.tsx の実装を参考にする（L162-176）
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent
- [x] Code review by codex MCP
- [x] Update docs/architecture/*.md
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing

## Notes

- SettingsPage.tsx には既に同様の実装がある：
```tsx
const LLM_PROVIDERS = [
  { value: 'ollama', label: 'Ollama' },
  { value: 'openai', label: 'OpenAI' },
]
```
