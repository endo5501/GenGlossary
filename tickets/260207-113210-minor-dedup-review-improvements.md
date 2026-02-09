---
priority: 4
tags: [improvement, backend, frontend]
description: "Minor improvements from dedup refactoring code review"
created_at: "2026-02-07T11:32:10Z"
started_at: 2026-02-09T14:21:35Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# Minor improvements from dedup refactoring code review

## 概要

除外用語/必須用語のコード重複削減リファクタリング後のコードレビューで指摘された軽微な改善点。

## 改善ポイント

### 1. generic_term_repository: add_term の None row ガード
`add_term` で INSERT が conflict 以外の理由で失敗した場合、後続の SELECT が None を返す可能性がある。`row["id"]` で TypeError になる。

### 2. useTermsCrud: undefined projectId のガード
`projectId` が `undefined` の状態で `refetch()` が呼ばれた場合、URL が `/api/projects/undefined/...` になる。

### 3. term_base_schemas: TermListResponseBase.items の型付け
`TermListResponseBase.items` が `list` (untyped) のため、OpenAPI スキーマの型情報が弱い。

## Tasks

- [x] generic_term_repository: add_term で row が None の場合のエラーハンドリング追加
- [x] useTermsCrud: projectId undefined 時の安全ガード追加
- [x] term_base_schemas: TermListResponseBase.items にジェネリック型を適用
- [x] Commit
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Update docs (glob: "*.md" in ./docs/architecture)
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing


## Design

### 1. generic_term_repository: None row ガード
- `row = cursor.fetchone()` の後に `if row is None:` のガードを追加
- `RuntimeError` を送出、テーブル名と term_text をエラーメッセージに含める

### 2. useTermsCrud: projectId undefined ガード
- 各フック内で `projectId` が undefined/falsy の場合に早期リターン
- リスト取得は空配列を返し、mutation系は何もしない

### 3. term_base_schemas: ジェネリック型の適用
- `TermListResponseBase` を `BaseModel, Generic[T]` に変更
- `items: list[T]` に型パラメータを適用
- サブクラスで具象型を指定

## Notes

- コードレビュー元チケット: 260207-110919-refactor-terms-dedup
- いずれも低優先度の改善で、現状の機能には影響しない
