---
priority: 4
tags: [bugfix, backend]
description: "Fix add_member_to_group misreporting FK errors as duplicate term conflict"
created_at: "2026-02-08T08:09:42Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# add_member_to_group FK エラーの誤報修正

## 概要

`add_member_to_group` APIで `sqlite3.IntegrityError` をすべて "term already belongs to a group" (409) としてマッピングしているが、存在しない `group_id` に対するFK違反も同じエラーメッセージになる。

## 問題点

- FK違反（存在しないgroup_id）が409 Conflictとして返される
- 正しくは404 Not Foundを返すべき

## Tasks

- [ ] group_id存在確認を追加し、FK違反と重複を区別する
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

- Codexレビューで発見 (synonym-integrity-fixes チケット内)
