---
priority: 2
tags: [improvement, backend, database, security]
description: "Document storage: Fix file_name storing full path instead of relative"
created_at: "2026-01-30T20:40:00Z"
started_at: 2026-01-30T13:40:45Z
closed_at: 2026-01-30T13:54:04Z
---

# Document storage: Fix file_name storing full path

## 概要

`documents` テーブルの `file_name` カラムに完全パスが保存されており、API/スキーマの期待と矛盾している問題を修正する。

## 現状の問題

### 問題箇所: `executor.py:275-277`

```python
# 完全パスが file_name に保存される
create_document(conn, document.file_path, document.content, content_hash)
```

### 影響

1. **API/スキーマの矛盾**: `file_name` は「パスなしのファイル名」を期待
2. **セキュリティ**: Files API やログを通じてサーバーパスが漏洩する可能性
3. **ポータビリティ**: 異なる環境でDBを移動した場合にパスが無効になる

## 提案する解決策

### オプション1: 相対パス使用

`doc_root` からの相対パスを保存する。

```python
import os
relative_path = os.path.relpath(document.file_path, doc_root)
create_document(conn, relative_path, document.content, content_hash)
```

**メリット**: シンプル、既存スキーマを変更不要
**デメリット**: doc_root が変わると無効になる

### オプション2: file_path カラム追加

`file_name`（ファイル名のみ）と `file_path`（完全または相対パス）を分離。

```sql
ALTER TABLE documents ADD COLUMN file_path TEXT;
```

**メリット**: 両方の情報を保持、柔軟性が高い
**デメリット**: スキーママイグレーションが必要

### オプション3: basename 使用

ファイル名のみを保存（パス情報は破棄）。

```python
import os
create_document(conn, os.path.basename(document.file_path), ...)
```

**メリット**: 最もシンプル
**デメリット**: 同名ファイルの衝突リスク（現状でも一部対処済み）

## 影響範囲

- `src/genglossary/runs/executor.py`
- `src/genglossary/db/document_repository.py`
- `src/genglossary/db/schema.py`（オプション2の場合）
- API レスポンス
- フロントエンド表示

## Tasks

- [x] 設計レビュー・承認 → オプション1（相対パス使用）を採用
- [x] 実装 → `os.path.relpath(document.file_path, doc_root)` を使用
- [x] スキーママイグレーション（必要な場合） → 不要
- [x] テストの更新 → `TestDocumentFilePathStorage` クラス追加
- [x] Commit → 693f317, d91c3ef
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket.
  - pathlib統一の提案 → 260130-filepath-handling-improvements チケットに記録
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket.
  - Windows互換性、OSセパレータ統一の提案 → 260130-filepath-handling-improvements チケットに記録
- [x] Update docs/architecture/*.md → database.md, runs.md 更新
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing

## Notes

- 260130-executor-improvements チケットから延期
- codex MCP レビューで Medium 優先度として指摘
- 追加改善点は 260130-filepath-handling-improvements チケットに記録
