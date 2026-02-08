---
priority: 4
tags: [improvement, llm-debug]
description: "デバッグロギングの全エントリーポイント一貫適用"
created_at: "2026-02-08T08:58:41Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# デバッグロギングの全エントリーポイント一貫適用

## 概要

`RunManager` のパイプラインパスではデバッグロギングが接続されているが、他のLLMクライアント生成パス（CLI直接実行、APIルーターなど）ではデバッグオプションが渡されていない。`LLM_DEBUG` 環境変数を設定しても、一部のパスでしかログが生成されない。

## 修正案

- `create_llm_client` 内で `Config().llm_debug` を直接参照するように集約する
- またはすべての呼び出し元で一貫してデバッグ引数を渡す

## Tasks

- [ ] 設計検討
- [ ] テスト作成
- [ ] 実装
- [ ] Commit
- [ ] Run static analysis (`pyright`) before reviewing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before reviewing and pass all tests (No exceptions)
- [ ] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Update docs (glob: "*.md" in ./docs/architecture)
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## Notes

- Codex MCPコードレビュー指摘事項 #7
