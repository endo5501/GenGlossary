---
priority: 3
tags: [feature, backend]
description: "DB progress update implementation"
created_at: "2026-01-30T09:45:00Z"
started_at: null
closed_at: null
---

# DB progress update implementation

## 概要

`_create_progress_callback` の `conn` パラメータが未使用。
パラメータを削除する。

## 背景

- `runs` テーブルには `progress_current`, `progress_total`, `current_step` カラムが存在
- `update_run_progress` 関数も `runs_repository.py` に実装済み
- しかし `_create_progress_callback` で `conn` を受け取りながら使用していない
- UIがポーリングに依存している場合、進捗が更新されない問題がある

## Tasks

- [ ] 調査と判断
- [ ] テストを追加・更新
- [ ] `conn` パラメータを削除し、進捗はSSEログのみで提供を実装
- [ ] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [ ] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Update docs/architecture/*.md
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing
