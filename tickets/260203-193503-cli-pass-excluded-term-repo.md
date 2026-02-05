---
priority: 2
tags: [enhancement, excluded-terms]
description: "CLI: pass excluded_term_repo to TermExtractor for consistency"
created_at: "2026-02-03T19:35:03Z"
started_at: 2026-02-05T14:27:10Z # Do not modify manually
closed_at: 2026-02-05T14:45:01Z # Do not modify manually
---

# CLI: pass excluded_term_repo to TermExtractor for consistency

## 概要

API経由での実行では`excluded_term_repo`が`TermExtractor`に渡されるようになったが、CLI経由での実行では渡されていない。一貫性のため、CLIでもDB使用時は同様に渡すべき。

## 背景

- `src/genglossary/runs/executor.py`で修正済み（API経由）
- `src/genglossary/cli.py`と`src/genglossary/cli_db.py`は未対応
- CLIでDBを使用する場合は、common_noun自動除外機能が動作すべき

## Tasks

- [x] `cli.py`でTermExtractor呼び出し時にDB接続を確認し、存在すれば`excluded_term_repo`として渡す
- [x] `cli_db.py`で同様の修正
- [x] テストの追加
- [x] Commit
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Update docs/architecture/*.md (変更不要 - 高レベルの説明のため)
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing


## Notes

- 関連チケット: 260203-192459-common-noun-auto-exclusion-not-working
- CLIでの非DBモードでは`excluded_term_repo=None`のままでOK
