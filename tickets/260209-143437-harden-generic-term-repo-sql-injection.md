---
priority: 4
tags: [security, backend]
description: "Harden generic_term_repository table parameter against SQL injection"
created_at: "2026-02-09T14:34:37Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# Harden generic_term_repository table parameter against SQL injection

## 概要

`generic_term_repository.py` の各関数で `table` パラメータがf-stringで直接SQL文に埋め込まれている。
現在は呼び出し元が定数（`terms_excluded` / `terms_required`）を渡しているため問題ないが、
将来的にユーザ入力由来の値が渡されるとSQL injection の脆弱性になる。

## 改善案

- `table` パラメータに許可リスト（Literal型 / Enum + ランタイムチェック）を導入
- 不正なテーブル名が渡された場合にエラーを送出

## Tasks

- [ ] table パラメータに allowlist を導入（Literal or Enum + runtime check）
- [ ] 不正なテーブル名に対するテスト追加
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

- codex MCP コードレビューで指摘された既存の問題
- 現時点では呼び出し元が定数を渡しているため実害なし
