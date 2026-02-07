---
priority: 1
tags: [improvement, backend, frontend]
description: "Code review findings from extract pipeline restructuring"
created_at: "2026-02-07T13:25:48Z"
started_at: 2026-02-07T13:38:28Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# Extract Pipeline リストラクチャリング コードレビュー指摘事項

## 概要

チケット `260207-095532-restructure-extract-pipeline-flow` のコードレビュー（codex MCP + code-simplifier agent）で発見された、即時対応しなかった改善項目をまとめたチケット。

## 指摘事項

### 1. エラーメッセージのサニタイズ (Codex #4 - Low)

`extract_skipped_reason` に生の例外メッセージ（Run ID等の内部情報）がそのままUIに表示される。

- `src/genglossary/api/routers/files.py:387`
- `frontend/src/components/dialogs/AddFileDialog.tsx:124`

**対応案**: ユーザー向けの固定メッセージに変換し、詳細はログに記録する。

### 2. scopeOptions の値重複 (Code-Simplifier #A)

`GlobalTopBar.tsx` で `scopeOptions` の値リストと `isRunScope` 型ガードで同じ値を2箇所定義。

- `frontend/src/components/layout/GlobalTopBar.tsx:16-25`

**対応案**: `scopeOptions.map(opt => opt.value)` から動的に生成。

### 3. ファイルサイズ上限の不整合 (Code-Simplifier #B)

フロントエンド `MAX_FILE_SIZE=5MB` vs バックエンド `MAX_CONTENT_BYTES=3MB`。

- `frontend/src/components/dialogs/AddFileDialog.tsx:34`
- `src/genglossary/api/routers/files.py:32`

**対応案**: 3MBへ値を統一し、可能であればバックエンドの設定をフロントエンドで共有。

### 4. N+1クエリ (Code-Simplifier #C)

作成後のファイルをループ内で個別にDB取得している。

- `src/genglossary/api/routers/files.py:374-378`

**対応案**: バッチ取得関数を追加するか、`create_document` が row を返すようにする。

### 5. fullスコープのAPI契約名 (Codex #3 - Medium)

`full` スコープの意味が変わった（extract除外）が、API名は `full` のまま。既存クライアントの回帰リスク。

**対応案**: ドキュメント更新で対応（API名変更は影響が大きいため）。現状CLIでの `full` 利用者への影響を確認。

## Tasks

- [x] エラーメッセージのサニタイズ
- [x] scopeOptions の重複排除
- [x] ファイルサイズ上限の統一
- [x] N+1クエリの改善
- [x] fullスコープのドキュメント・API整合性確認（既にドキュメント更新済み）
- [x] Commit
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Update docs/architecture/*.md（既に正確に記述済み、追加変更不要）
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing


## 設計

### 1. エラーメッセージのサニタイズ
- **方針**: 固定メッセージに置換
- `src/genglossary/api/routers/files.py`: `str(e)` → ユーザー向け固定メッセージ（「抽出処理をスキップしました」）
- 生の例外は `logger.warning()` でログに記録
- フロントエンド側の変更は不要（表示されるメッセージが安全になるため）

### 2. N+1クエリの改善
- **方針**: `create_document` が row を返すように変更
- DB層の `create_document` の戻り値を `doc_id` → `Row` に変更
- `create_files_bulk` のループ内 `get_document()` 呼び出しを削除し、`create_document` の戻り値を直接使用

### 3. ファイルサイズ上限の統一
- **方針**: フロントエンドを3MBに統一
- `AddFileDialog.tsx` の `MAX_FILE_SIZE` を `5MB` → `3MB` に変更

### 4. scopeOptions の重複排除
- **方針**: `scopeOptions` から動的生成
- `isRunScope` の値リストを `scopeOptions.map(opt => opt.value)` から生成

### 5. fullスコープのドキュメント更新
- **方針**: ドキュメント更新のみ（API名変更なし）
- `full` スコープが「generate → review → refine」（extractを含まない）ことを明記

### 実行順
1. エラーメッセージのサニタイズ（TDD）
2. N+1クエリの改善（TDD）
3. ファイルサイズ上限の統一
4. scopeOptions の重複排除
5. fullスコープのドキュメント更新

## Notes

- Codex #3 (fullスコープ名) と Code-Simplifier #D (責務分離) は設計判断として現状維持が妥当な可能性あり。チケット開始時に要検討。
- 即時修正済み: Codex #1 (非RuntimeError で500エラー), #2 (広範なexceptキャッチ), #5 (テストカバレッジ) → commit `3febf12`
