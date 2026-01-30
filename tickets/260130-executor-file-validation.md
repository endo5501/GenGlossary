---
priority: 2
tags: [improvement, backend, executor, security]
description: "PipelineExecutor: Add file validation and size limits for document loading"
created_at: "2026-01-30T20:50:00Z"
started_at: 2026-01-30T13:55:28Z
closed_at: null
---

# PipelineExecutor: File validation and size limits

## 概要

ドキュメント読み込み時のバリデーションとサイズ制限を追加し、セキュリティとリソース保護を強化する。

## 現状の問題

**問題箇所**: `executor.py:266-277`

```python
loader = DocumentLoader()
documents = loader.load_directory(doc_root)
# ファイルサイズや種類の検証なし

for document in documents:
    create_document(conn, document.file_path, document.content, content_hash)
```

## 影響

1. **セキュリティ**: `doc_root` がユーザー制御の場合（GUI）、任意のファイルシステムパスを読み込み可能
2. **リソース消費**: 巨大ファイルを読み込むとメモリ/DB が膨張
3. **機密情報漏洩**: `.env`, `credentials.json` 等の機密ファイルが読み込まれる可能性

## 提案する解決策

### 1. ファイルサイズ制限

```python
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def load_file(self, path):
    if os.path.getsize(path) > MAX_FILE_SIZE:
        raise ValueError(f"File too large: {path}")
```

### 2. パス検証（ディレクトリトラバーサル防止）

```python
def _validate_path(doc_root: str, file_path: str) -> bool:
    real_root = os.path.realpath(doc_root)
    real_path = os.path.realpath(file_path)
    return real_path.startswith(real_root)
```

### 3. 機密ファイル除外

```python
EXCLUDED_PATTERNS = ['.env', 'credentials*', '*.key', '*.pem']
```

### 4. 許可された拡張子のみ

```python
ALLOWED_EXTENSIONS = ['.txt', '.md', '.rst', '.html']
```

## 影響範囲

- `src/genglossary/document_loader.py`
- `src/genglossary/runs/executor.py`
- 設定ファイル（制限値の設定）

## Tasks

- [x] 設計
- [x] DocumentLoader にバリデーション追加
- [x] 設定可能な制限値
- [x] テスト更新
- [x] Commit
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket.
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket.
- [x] Update docs/architecture/*.md
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing

## Notes

- codex MCP レビューで Low 優先度として指摘
- GUI 経由でのファイルアップロードにも適用すべき
