---
priority: 7
tags: [improvement, backend, database, security]
description: "Document storage: Fix file_name storing full path instead of relative"
created_at: "2026-01-30T20:40:00Z"
started_at: null
closed_at: null
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

- [ ] 設計レビュー・承認
- [ ] 実装
- [ ] スキーママイグレーション（必要な場合）
- [ ] テストの更新
- [ ] ドキュメント更新

## Notes

- 260130-executor-improvements チケットから延期
- codex MCP レビューで Medium 優先度として指摘
