---
priority: 2
tags: [bug, performance, extraction]
description: "ファイル登録時、新規追加ファイルのみを対象に用語抽出を行うよう改善する"
created_at: "2026-02-09T15:10:04Z"
started_at: 2026-02-09T22:52:04Z # Do not modify manually
closed_at: 2026-02-10T12:01:08Z # Do not modify manually
---

# ファイル登録時、新規追加ファイルのみを対象に用語抽出を行う

## 問題

現在、WebUIからファイルを一括登録（`POST /api/projects/{project_id}/files/bulk`）すると、自動的に用語抽出が開始される。しかし、この用語抽出処理では**新規追加したファイルだけでなく、すでに登録済みの全ファイル**を対象に抽出を行っている。

これにより以下の問題が発生する：
- ファイル追加のたびに全ファイルを対象にLLMへ問い合わせるため、**不要なAPI呼び出し**が発生する
- 登録済みファイルの用語は既に抽出済みであるにも関わらず、再度処理される
- ファイル数が増えるほど、登録時の処理時間が増大する

## 原因

`executor.py` の `_load_documents()` メソッド（行378-431）で `list_all_documents(conn)` を呼び出し、`documents` テーブルの**全レコード**を取得している。

```
executor.py:_load_documents()
  → document_repository.py:list_all_documents()
    → SELECT * FROM documents ORDER BY id  （全件取得）
```

ファイル登録時のフロー:
1. `files.py` (行304-389): `POST /files/bulk` で新規ファイルをDB登録
2. `files.py` (行375-383): `manager.start_run(scope="extract")` を自動トリガー
3. `manager.py` → `executor.py`: バックグラウンドで抽出処理開始
4. `executor.py:_load_documents()`: **全登録ファイルを取得** ← ここが問題
5. 全ファイルを対象に用語抽出を実行

## 改善方針

ファイル登録時に自動トリガーされる用語抽出では、**今回追加されたファイルのみ**を抽出対象とする。

### 考えられるアプローチ

1. `start_run()` に対象ドキュメントIDリストを渡せるようにする
2. `_load_documents()` がドキュメントIDリストでフィルタリングできるようにする
3. bulk upload時に新規追加されたドキュメントIDを取得し、抽出対象として渡す

## 関連ファイル

- `src/genglossary/api/routers/files.py` - ファイル登録エンドポイント
- `src/genglossary/runs/manager.py` - 実行管理（start_run）
- `src/genglossary/runs/executor.py` - パイプライン実行（_load_documents, _execute_extract）
- `src/genglossary/db/document_repository.py` - ドキュメントDB操作（list_all_documents）

## Tasks

- [x] 調査：現在の用語抽出フローの詳細確認
- [x] 設計：対象ドキュメント絞り込みの実装方針決定
- [x] 実装：ドキュメントIDリストによるフィルタリング機能追加
- [x] 実装：bulk upload時に新規ドキュメントIDを抽出対象として渡す
- [x] テスト：新規ファイルのみが抽出対象となることを確認
- [x] テスト：既存の全ファイル対象の抽出（手動実行）が引き続き動作することを確認
- [x] Commit
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Update docs (glob: "*.md" in ./docs/architecture)
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing

## 設計（確定）

`start_run()` にオプショナルな `document_ids` パラメータを追加し、指定時はそのドキュメントのみを対象に抽出する。

### 変更箇所

1. **`document_repository.py`**: `list_documents_by_ids(conn, ids)` を新設
2. **`manager.py`**: `start_run()` に `document_ids` パラメータ追加、executor まで伝播
3. **`executor.py`**: `execute()` に `document_ids` パラメータ追加。指定時は `_clear_tables_for_scope()` をスキップし、IDリストでフィルタリングしたドキュメントのみ取得
4. **`files.py`**: bulk upload で新規ドキュメントIDを収集し `start_run()` に渡す

### 動作パターン
- **自動トリガー（bulk upload）**: `document_ids` あり → 新規ファイルのみ抽出、既存termsは保持
- **手動実行（API）**: `document_ids` なし → 従来通り全ファイル対象、termsクリア後に再抽出

## Notes

- 手動で「全体抽出」を実行するケース（WebUIの再実行ボタンなど）では、従来通り全ファイルを対象とする必要がある
- `scope="extract"` の実行には「全体対象」と「特定ファイル対象」の2パターンが必要になる可能性がある
