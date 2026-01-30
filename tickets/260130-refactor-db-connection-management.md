---
priority: 1
tags: [refactoring, backend, database]
description: "Refactor database connection management to eliminate duplication"
created_at: "2026-01-30T22:15:00Z"
started_at: null
closed_at: null
---

# Refactor database connection management to eliminate duplication

## 概要

`database_connection()` コンテキストマネージャの実装が複数箇所に散在しており、DRY原則に違反している。統一化により保守性を向上させる。

## 現状の問題

### 重複コード

1. **connection.py (69-89行目)**
   - `database_connection()` が定義されているが、あまり使われていない

2. **manager.py (56-67行目)**
   - `_db_connection()` が独自に実装されている

3. **cli_db.py (77-98行目)**
   - `_db_operation()` が独自に実装されている（エラーハンドリング付き）

### 散在する手動接続管理

cli_db.py の多くのコマンドで、手動で接続を取得・クローズしている:
- `terms_list()`, `terms_show()`, `terms_update()`, `terms_delete()`, `terms_import()` など

## 提案する解決策

1. `connection.py` の `database_connection()` を標準的な接続管理として使用
2. `manager.py` の `_db_connection()` を削除し、`database_connection()` を使用
3. `cli_db.py` のすべてのコマンドで一貫したパターンを使用

## 影響範囲

- src/genglossary/db/connection.py
- src/genglossary/runs/manager.py
- src/genglossary/cli_db.py
- src/genglossary/api/routers/projects.py (`_get_project_statistics`)

## Tasks

- [ ] 設計レビュー・承認
- [ ] manager.py の _db_connection() を database_connection() に置き換え
- [ ] cli_db.py のコマンドで一貫したパターンを使用
- [ ] projects.py の _get_project_statistics を改善
- [ ] Commit
- [ ] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest`) before reviwing and pass all tests (No exceptions)
- [ ] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket.
- [ ] Code review by codex MCP. If the issue is not addressed immediately, create a ticket.
- [ ] Update docs/architecture/*.md
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## Notes

- 260130-repository-transaction-safety チケットのレビューで発見
- 機能には問題なし、保守性向上のためのリファクタリング
