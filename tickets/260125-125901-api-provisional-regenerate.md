---
priority: 4.7
tags: [api, llm, provisional]
description: "Implement provisional glossary entry regeneration endpoint with LLM integration"
created_at: "2026-01-25T12:59:01Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# Ticket Overview

Implement the `POST /api/projects/{project_id}/provisional/{entry_id}/regenerate` endpoint
that currently returns TODO placeholder. This endpoint should use LLM (Ollama) to
regenerate a single provisional glossary entry's definition and confidence score.

This is a follow-up from ticket #260124-164009-gui-api-data-endpoints code review.


## Tasks

- [ ] **Red**: テスト追加
  - [ ] regenerate が実際に定義を変更することを検証するテスト
  - [ ] regenerate が confidence を更新することを検証するテスト
  - [ ] LLM呼び出しのモックを使用したテスト
- [ ] テスト失敗確認（Red完了）
- [ ] **Implementation**: regenerate endpoint実装
  - [ ] LLM client (GlossaryGenerator) を使用して定義を再生成
  - [ ] プロジェクトのLLM設定を取得して使用
  - [ ] ドキュメントコンテキストを読み込んで渡す
  - [ ] 再生成結果をDBに保存
- [ ] **Green**: テスト通過確認
- [ ] Code simplification review using code-simplifier agent
- [ ] Update docs/architecture.md (API エンドポイントの説明を更新)
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing


## Notes

### 現状の問題
- `src/genglossary/api/routers/provisional.py:101-128` が TODO で既存値を返している
- `tests/api/routers/test_provisional.py:172-182` が「再生成されたこと」を検証していない

### 実装方針
- LLM統合パターンは `/llm-integration` スキルを参照
- GlossaryGenerator を使用して単一エントリを再生成
- エラーハンドリング（LLMタイムアウト、API失敗など）を適切に実装
- 既存のCLI実装 (`cli_db_regenerate.py`) を参考にする

### Dependencies
- Ticket #260124-164009-gui-api-data-endpoints (完了済み)
- LLM設定がプロジェクトに保存されていること
