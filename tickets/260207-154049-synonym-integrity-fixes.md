---
priority: 2
tags: [bugfix, backend, api]
description: "Fix synonym group integrity issues found during code review"
created_at: "2026-02-07T15:40:49Z"
started_at: 2026-02-08T07:48:37Z # Do not modify manually
closed_at: 2026-02-08T08:16:02Z # Do not modify manually
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

- [x] メンバー削除APIでgroup_id検証を追加
- [x] 代表語変更時のメンバー存在確認を追加
- [x] 代表語のメンバー削除を禁止またはグループ削除
- [x] issueテーブルに should_exclude, exclusion_reason カラムを追加
- [x] APIスキーマにvalidate_term_textバリデーションを追加
- [x] list_groups をJOINベースに最適化
- [x] 同義語ルックアップロジックを共通化
- [x] Commit
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Update docs (glob: "*.md" in ./docs/architecture)
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing


## 設計

### 問題1: メンバー削除APIでgroup_id検証

- `synonym_repository.py` の `remove_member()` に `group_id` 引数を追加
- 削除前にメンバーの所属group_idとURLのgroup_idの一致を検証
- 不一致時は例外を送出
- APIルーター側も `group_id` を渡すように変更

### 問題2: 代表語の整合性保護

**2a. 代表語変更時のメンバー存在確認**
- `update_primary_term()` で新しい `primary_term_text` がグループのメンバーに存在するか検証
- 存在しない場合は `ValueError` を送出、API側で HTTP 400 にマッピング

**2b. 代表語のメンバー削除 → グループ全体削除**
- `remove_member()` 内で、削除対象が `primary_term_text` と一致する場合はグループ全体を削除
- APIレスポンスは変わらず 204

### 問題3: glossary_issuesテーブルにカラム追加

- スキーマバージョン 8 → 9
- `ALTER TABLE glossary_issues ADD COLUMN should_exclude INTEGER NOT NULL DEFAULT 0`
- `ALTER TABLE glossary_issues ADD COLUMN exclusion_reason TEXT`
- `issue_repository.py` の保存・読み取りで新カラムを対応

### 問題4: APIスキーマのバリデーション統一

- リクエストスキーマに `validate_term_text` バリデータを追加
- モデル側と同様に `strip()` 後の空文字チェック

### 問題5: list_groups の N+1 クエリ解消

- JOINで1クエリに統合
- Python側で `SynonymGroup` リストに組み立て

### 問題6: 同義語ルックアップロジックのDRY化

- `src/genglossary/synonym_utils.py` を新規作成
- 共通関数: `build_synonym_lookup()`, `build_non_primary_set()`, `get_synonyms_for_primary()`
- 4ファイル（generator, reviewer, refiner, markdown_writer）の重複ロジックを置き換え

## Notes

- 問題1-3はfull pipeline実行では顕在化しにくいが、分離実行やAPI直接呼び出しで問題になる
- 問題6はリファクタリングなので機能的な影響なし
