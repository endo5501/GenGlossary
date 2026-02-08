---
priority: 1
tags: [bugfix, backend]
description: "Required terms should override excluded terms in term list and extraction"
created_at: "2026-02-08T05:23:51Z"
started_at: 2026-02-08T07:22:03Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# 必須用語が除外用語より優先されるようにする

## 概要

除外用語と必須用語の両方に同一の用語が含まれている場合、現状では除外用語が優先され、用語一覧にも表示されず解析もされない。必須用語は「必ず含める」という意図があるため、除外用語より優先されるべき。

## 再現手順

1. 除外用語一覧に「用語A」を追加する
2. 必須用語一覧に「用語A」を追加する
3. Terms画面の用語一覧を確認する → 「用語A」が表示されない
4. 用語抽出を実行する → 「用語A」が解析対象に含まれない

## 期待される動作

- 同一用語が除外・必須の両方に存在する場合、必須用語が優先される
- 必須用語は常に用語一覧に表示される
- 必須用語は常に用語抽出・解析の対象となる

## 調査結果

### 用語一覧表示（`list_all_terms`）- **修正必要**
- `src/genglossary/db/term_repository.py` の `list_all_terms()` SQLクエリにバグ
- 1つ目のSELECT: `terms_extracted` から除外する際、`terms_required` に含まれる用語も除外してしまう
- 2つ目のSELECT: `terms_required` のうち `terms_excluded` に含まれるものも除外してしまう
- 既存テスト `test_required_term_excluded_when_in_excluded_list`, `test_mixed_extracted_and_required_terms` がバグの挙動をアサートしているため、テストの期待値も修正が必要

### 用語抽出処理（`TermExtractor`）- **修正不要**
- `_filter_excluded_terms()` は既に `required` をオーバーライドする実装済み
- テスト `test_required_overrides_excluded` で動作確認済み

## 修正方針

### SQLクエリ修正（`list_all_terms`）
1. 1つ目のSELECT: 除外フィルタに `terms_required` にある場合は除外しない条件を追加
2. 2つ目のSELECT: `NOT EXISTS terms_excluded` 条件を削除（必須用語は常に表示）

### テスト修正
- `test_required_term_excluded_when_in_excluded_list`: `not in` → `in` に変更
- `test_mixed_extracted_and_required_terms`: 「除外される必須用語」が含まれるようにし、`len(terms) == 4` に修正

## Tasks

- [x] 原因調査：影響箇所の特定と修正方針の確定
- [x] テスト修正（TDD: Red）
- [x] 修正実装（list_all_terms）
- [x] Commit
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Update docs (glob: "*.md" in ./docs/architecture)
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing


## Notes

- 必須用語は「必ず含める」という明示的な意図を持つため、除外用語より優先度が高いと考える
- 既存の抽出処理（`_merge_required_terms`）では必須用語を候補にマージしているが、その前段の除外フィルタで落とされている可能性がある
