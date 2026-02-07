---
priority: 2
tags: [feature, backend, debug]
description: "Add LLM debug mode to log prompts and responses for troubleshooting"
created_at: "2026-02-07T16:09:22Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# LLMデバッグログ機能の追加

## 概要

現在、LLMに送信しているプロンプトや受信したレスポンスの内容を確認する手段がない。適切なプロンプトが送受信されているかを検証するためのデバッグ機能を追加する。

## ユースケース

- プロンプトの内容が意図通りか確認したい
- LLMからのレスポンスが期待通りか確認したい
- 用語集生成の品質問題を調査したい
- 同義語情報やuser_notesがプロンプトに正しく含まれているか確認したい

## 実装案

`--llm-debug` フラグ付きでバックエンドを起動すると、LLMとの送受信内容をファイルに出力する。

```bash
# 例：デバッグモードで起動
uv run genglossary serve --llm-debug

# 出力先：output/llm-debug/ 等
# ファイル例：
#   output/llm-debug/001-extract-request.txt
#   output/llm-debug/001-extract-response.txt
#   output/llm-debug/002-generate-request.txt
#   output/llm-debug/002-generate-response.txt
```

## Tasks

- [ ] 設計検討（出力形式、出力先、有効化方法）
- [ ] LLMクライアントにデバッグログ機能を追加
- [ ] CLIに `--llm-debug` オプションを追加
- [ ] パイプライン各ステップでのデバッグ出力対応
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

- 本番運用では無効にすべき（デフォルトOFF）
- ログファイルにはセンシティブな情報が含まれる可能性があるため、.gitignoreに追加推奨
- 将来的にはWeb UIからもデバッグログを閲覧できるようにすることも検討可能
