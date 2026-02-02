---
priority: 5
tags: [frontend, refactoring]
description: "LLM設定UI（OllamaモデルSelect/TextInput）の共通コンポーネント化"
created_at: "2026-02-02T13:52:35Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
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

- [ ] `frontend/src/constants/llm.ts` を作成し、LLM関連の定数を集約
- [ ] `frontend/src/components/inputs/OllamaModelInput.tsx` コンポーネントを作成
- [ ] SettingsPage を OllamaModelInput を使用するようリファクタリング
- [ ] CreateProjectDialog を OllamaModelInput を使用するようリファクタリング
- [ ] (Optional) `useLlmSettings` カスタムフックの作成
- [ ] Commit
- [ ] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [ ] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Update docs/architecture/*.md
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing


## Notes

- code-simplifier agent のレビュー結果に基づくリファクタリング
- バックエンドの OllamaClient._fetch_tags() メソッド抽出も検討（低優先度）
