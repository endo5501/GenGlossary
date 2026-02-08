---
priority: 4
tags: [improvement, llm-debug]
description: "generate_structured のデバッグログに実効プロンプトを記録する"
created_at: "2026-02-08T08:58:36Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# generate_structured のデバッグログに実効プロンプトを記録する

## 概要

`generate_structured` ラッパーは元の `prompt` 引数をログに記録するが、実際にLLMに送られるのは `_build_json_prompt()` で加工された `json_prompt` である。デバッグログが実際のリクエスト内容を正確に反映していない。

## 修正案

- ラッパーで実効プロンプト（加工後のもの）をログに記録する
- または、具体的なクライアントのメソッド内でログ記録を行う

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

- Codex MCPコードレビュー指摘事項 #3
