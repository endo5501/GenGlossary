---
priority: 2
tags: [bugfix, backend, api]
description: "Fix synonym group integrity issues found during code review"
created_at: "2026-02-07T15:40:49Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# 同義語グループ整合性修正

## 概要

同義語リンク機能のコードレビューで発見された整合性の問題を修正する。

## 問題点

### 1. メンバー削除APIがgroup_idを検証していない（High）
- `DELETE /synonym-groups/{A}/members/{member_id}` でURLのgroup_id Aと実際のmember所属グループが異なっていても削除が成功する
- 対策: `remove_member` でgroup_id一致を検証

### 2. 代表語の整合性が崩れる操作が可能（High）
- `primary_term_text` をメンバー外の値に更新可能
- 代表語をメンバーから削除可能
- 対策: 代表語変更時のメンバー存在確認、代表語の削除禁止（または別メンバーへの自動昇格）

### 3. review→refine分離実行時にshould_excludeが失われる（High）
- `glossary_issues` テーブルに `should_exclude` / `exclusion_reason` が保存されていない
- 分離実行時に除外指示が復元されない
- 対策: issueテーブルスキーマにカラム追加

### 4. APIスキーマのバリデーション不一致（Medium）
- API schemas (`synonym_group_schemas.py`) は `min_length=1` のみ
- Pydanticモデル (`synonym.py`) では `validate_term_text` でトリム検証あり
- 空白のみ文字列がDBに入る可能性

### 5. list_groups の N+1 クエリ（Low）
- グループごとにメンバーを別クエリで取得
- JOIN + Python集約に置き換え可能

### 6. 同義語ルックアップロジックのDRY化（Low）
- 4ファイル (generator, reviewer, refiner, markdown_writer) で同じルックアップ構築パターンが重複
- 共通ユーティリティに抽出推奨

## Tasks

- [ ] メンバー削除APIでgroup_id検証を追加
- [ ] 代表語変更時のメンバー存在確認を追加
- [ ] 代表語のメンバー削除を禁止またはグループ削除
- [ ] issueテーブルに should_exclude, exclusion_reason カラムを追加
- [ ] APIスキーマにvalidate_term_textバリデーションを追加
- [ ] list_groups をJOINベースに最適化
- [ ] 同義語ルックアップロジックを共通化
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

- 問題1-3はfull pipeline実行では顕在化しにくいが、分離実行やAPI直接呼び出しで問題になる
- 問題6はリファクタリングなので機能的な影響なし
