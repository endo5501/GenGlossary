---
priority: 5
tags: [frontend, refactoring]
description: "LLM設定UI（OllamaモデルSelect/TextInput）の共通コンポーネント化"
created_at: "2026-02-02T13:52:35Z"
started_at: 2026-02-02T16:36:15Z # Do not modify manually
closed_at: 2026-02-02T22:04:29Z # Do not modify manually
---

# LLM設定UIコンポーネントの共通化

## 概要

SettingsPage と CreateProjectDialog で重複している LLM 設定 UI ロジックを共通コンポーネントに抽出する。

## 背景

Ollama モデルドロップダウン機能の実装（#260201-124808）で、以下の重複が発生：
- Ollamaモデルの表示/非表示条件
- SelectとTextInputの切り替えロジック
- LoadingとErrorの処理
- プロバイダー変更時のBase URL設定ロジック
- DEFAULT_OLLAMA_BASE_URL 定数の重複定義

## Tasks

- [x] `frontend/src/constants/llm.ts` を作成し、LLM関連の定数を集約
- [x] `frontend/src/components/inputs/LlmSettingsForm.tsx` コンポーネントを作成（テストファースト）
- [x] SettingsPage を LlmSettingsForm を使用するようリファクタリング
- [x] CreateProjectDialog を LlmSettingsForm を使用するようリファクタリング
- [x] Commit
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Update docs/architecture/*.md
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing

## Design

### ファイル構成

```
frontend/src/
├── constants/
│   └── llm.ts                      # 新規: LLM関連定数
└── components/
    └── inputs/
        └── LlmSettingsForm.tsx     # 新規: LLM設定フォーム
```

### 定数ファイル (`constants/llm.ts`)

```typescript
export const DEFAULT_OLLAMA_BASE_URL = 'http://localhost:11434'

export const LLM_PROVIDERS = [
  { value: 'ollama', label: 'Ollama' },
  { value: 'openai', label: 'OpenAI' },
] as const
```

### コンポーネントインターフェース

```typescript
interface LlmSettingsFormProps {
  // 値
  provider: string
  model: string
  baseUrl: string

  // 変更ハンドラー
  onProviderChange: (provider: string) => void
  onModelChange: (model: string) => void
  onBaseUrlChange: (baseUrl: string) => void

  // オプション: ラベルのカスタマイズ
  modelLabel?: string  // デフォルト: "Model"
}
```

### 内部動作

- `useOllamaModels` フックを内部で使用
- プロバイダー変更時、`ollama` なら自動的に `onBaseUrlChange(DEFAULT_OLLAMA_BASE_URL)` を呼ぶ
- エラーアラート、Select/TextInput 切り替えをすべて内部で処理

### レンダリング内容

```
┌─────────────────────────────────────┐
│ Provider (Select)                   │
│ [Ollama ▼]                          │
├─────────────────────────────────────┤
│ Base URL (TextInput)                │
│ [http://localhost:11434]            │
│ 説明: Ollama server URL             │
├─────────────────────────────────────┤
│ ⚠ Ollamaサーバーに接続できません     │  ← エラー時のみ表示
│   モデル名を手動で入力してください    │
├─────────────────────────────────────┤
│ Model (Select or TextInput)         │
│ [llama3.2 ▼] または [____入力____]   │
└─────────────────────────────────────┘
```

### 使用例

**SettingsPage.tsx:**
```tsx
<LlmSettingsForm
  provider={provider}
  model={model}
  baseUrl={baseUrl}
  onProviderChange={setProvider}
  onModelChange={setModel}
  onBaseUrlChange={setBaseUrl}
/>
```

**CreateProjectDialog.tsx:**
```tsx
<LlmSettingsForm
  provider={llmProvider}
  model={llmModel}
  baseUrl={baseUrl}
  onProviderChange={setLlmProvider}
  onModelChange={setLlmModel}
  onBaseUrlChange={setBaseUrl}
  modelLabel="LLM Model"
/>
```

## Notes

- code-simplifier agent のレビュー結果に基づくリファクタリング
- useLlmSettings カスタムフックは YAGNI 原則により作成しない
- バックエンドの OllamaClient._fetch_tags() メソッド抽出も検討（低優先度）
