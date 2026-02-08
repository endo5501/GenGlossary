---
priority: 4
tags: [bugfix, backend]
description: "Enforce primary_term_text must be in member_texts when creating synonym group"
created_at: "2026-02-08T08:10:01Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# create_group で primary_term_text のメンバー存在検証

## 概要

`create_group()` で `primary_term_text` が `member_texts` に含まれていることを検証していない。primary がメンバーに含まれていないグループが作成されると、後続の remove_member での primary 削除ロジックが正しく動作しない。

## Tasks

- [ ] create_group で primary_term_text が member_texts に含まれることを検証
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
