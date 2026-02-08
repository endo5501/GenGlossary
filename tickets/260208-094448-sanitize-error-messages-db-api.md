---
priority: 4
tags: [improvement, backend, security]
description: "Sanitize error messages before DB persistence and API exposure"
created_at: "2026-02-08T09:44:48Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# Sanitize error messages before DB persistence and API exposure

## 概要

Codex MCPレビューで指摘。RunManagerの `error_message` フィールドには生の例外テキストが保存され、APIレスポンスとしてそのまま返される（`run_schemas.py:37`）。ファイルシステムパス、ホスト名等の機密情報が漏洩するリスクがある。

## 現状の問題

- `runs.error_message` は `TEXT` 型で長さ制限なし（`schema.py:111`）
- 例外の `str(e)` がそのままDBに保存される
- APIレスポンスでそのまま返される
- `str(e)` が空の場合、末尾にコロンが残る不自然なメッセージになる

## 提案する対処

1. DB保存前にサニタイズ（制御文字除去、機密トークンマスキング、長さ制限512-2048文字）
2. `str(e)` が空の場合は例外クラス名にフォールバック（例: `"Failed to start execution thread (RuntimeError)"`）
3. 非UTF-8文字の防御的正規化（`msg.encode("utf-8", "replace").decode("utf-8")`）

## Tasks

- [ ] 設計レビュー・承認
- [ ] 実装
- [ ] テストの更新
- [ ] Commit
- [ ] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [ ] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Update docs (glob: "*.md" in ./docs/architecture)
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## Notes

- 260202-225133チケットのcodex MCPレビューで指摘
- 関連ファイル: `src/genglossary/runs/manager.py`, `src/genglossary/api/schemas/run_schemas.py`, `src/genglossary/db/schema.py`
