---
priority: 2
tags: [bugfix, backend]
description: "Synonym group validation improvements: FK error reporting and primary member validation"
created_at: "2026-02-08T08:09:42Z"
started_at: 2026-02-08T10:17:50Z # Do not modify manually
closed_at: 2026-02-08T10:36:44Z # Do not modify manually
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

- [x] group_id存在確認を追加し、FK違反と重複を区別する
- [x] create_group で primary_term_text が member_texts に含まれることを検証
- [x] Commit
- [x] Run static analysis (`pyright`) before reviewing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before reviewing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Update docs (glob: "*.md" in ./docs/architecture)
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing

## 設計

### バグ1: add_member FK エラー区別

- `synonym_repository.py` に `GroupNotFoundError` 例外クラスを追加
- `add_member` でINSERT前に `group_id` の存在を SELECT で確認
- 存在しなければ `GroupNotFoundError` を発生
- API層で `GroupNotFoundError` を捕捉して 404 を返す
- 既存の `IntegrityError` は引き続き 409（重複）

### バグ2: create_group primary_term_text 検証

- `SynonymGroupCreateRequest` に `model_validator` を追加
- `primary_term_text` が `member_texts` に含まれていなければ `ValueError` を発生
- FastAPI が自動的に 422 を返す

### 変更ファイル

1. `src/genglossary/db/synonym_repository.py` - `GroupNotFoundError` + `add_member` 修正
2. `src/genglossary/api/routers/synonym_groups.py` - `GroupNotFoundError` の捕捉追加
3. `src/genglossary/api/schemas/synonym_group_schemas.py` - `model_validator` 追加
4. `tests/db/test_synonym_repository.py` - テスト追加
5. `tests/api/routers/test_synonym_groups.py` - テスト追加

### テスト計画

- リポジトリ: 存在しない `group_id` で `GroupNotFoundError` が発生
- API: 存在しない `group_id` へのPOSTで 404
- スキーマ: `primary_term_text` が `member_texts` に含まれないとバリデーションエラー
- API: `primary_term_text` が `member_texts` に含まれないPOSTで 422

## Notes

- Codexレビューで発見 (synonym-integrity-fixes チケット内)
- 統合元チケット: 260208-081001-create-group-primary-member-validation
