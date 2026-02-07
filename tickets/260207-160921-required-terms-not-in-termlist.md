---
priority: 1
tags: [bugfix, frontend, backend]
description: "Required terms not reflected in term list, preventing synonym group assignment"
created_at: "2026-02-07T16:09:21Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# 必須用語が用語一覧に反映されず同義語グループに追加できない

## 概要

必須用語一覧に追加した用語が、Terms画面の用語一覧に反映されていない。そのため、必須用語を同義語グループのメンバーとして追加することができない。

## 再現手順

1. 必須用語一覧に用語を追加する
2. Terms画面の用語一覧を確認する → 必須用語が表示されない
3. 同義語グループを作成し、必須用語をメンバーに追加しようとする → 候補に表示されない

## 期待される動作

- 必須用語一覧に追加した用語がTerms画面の用語一覧にも反映される
- 必須用語を同義語グループのメンバーとして追加できる

## Tasks

- [ ] 原因調査：必須用語がTerms画面に表示されない理由を特定
- [ ] 修正実装
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

- 必須用語一覧（required_terms）と抽出用語一覧（terms_extracted）のデータソースが異なるため、用語一覧のクエリが必須用語を含んでいない可能性が高い
