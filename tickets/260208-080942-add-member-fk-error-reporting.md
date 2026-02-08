---
priority: 2
tags: [bugfix, backend]
description: "Synonym group validation improvements: FK error reporting and primary member validation"
created_at: "2026-02-08T08:09:42Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# Synonym group バリデーション改善

## 概要

Synonym group 関連の2つのバグ修正を統合したチケット。

## 改善ポイント

### 1. add_member_to_group FK エラーの誤報修正

`add_member_to_group` APIで `sqlite3.IntegrityError` をすべて "term already belongs to a group" (409) としてマッピングしているが、存在しない `group_id` に対するFK違反も同じエラーメッセージになる。

- FK違反（存在しないgroup_id）が409 Conflictとして返される
- 正しくは404 Not Foundを返すべき

### 2. create_group で primary_term_text のメンバー存在検証

`create_group()` で `primary_term_text` が `member_texts` に含まれていることを検証していない。primary がメンバーに含まれていないグループが作成されると、後続の remove_member での primary 削除ロジックが正しく動作しない。

## Tasks

- [ ] group_id存在確認を追加し、FK違反と重複を区別する
- [ ] create_group で primary_term_text が member_texts に含まれることを検証
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

- Codexレビューで発見 (synonym-integrity-fixes チケット内)
- 統合元チケット: 260208-081001-create-group-primary-member-validation
