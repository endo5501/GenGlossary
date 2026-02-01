---
priority: 4
tags: [improvement, backend, security]
description: "API path validation: reject absolute paths and normalize input"
created_at: "2026-02-01T08:41:14Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# API path validation enhancement

## 概要

codex MCP のコードレビューで指摘された問題。

Files API の `_validate_file_name()` が以下のケースを適切に処理していない:

1. 絶対パス（`/etc/passwd.md`）を受け入れてしまう
2. パス正規化がない（`a/./b.md` と `a/b.md` が別物として扱われる）

## 問題点

### 1. 絶対パスの受け入れ

- `/etc/passwd.md` のような絶対パスが許可される
- スキーマドキュメントの "relative path" 要件に違反
- ポータビリティの問題

### 2. パス正規化の欠如

- `a/./b.md` と `a/b.md` が別のファイルとして登録可能
- 重複チェックをすり抜ける
- ルックアップ時の不整合

## 影響箇所

- `src/genglossary/api/routers/files.py:28-66`

## 推奨修正

```python
from pathlib import PurePosixPath

def _validate_file_name(file_name: str) -> str:
    """Validate and normalize file name (relative POSIX path).

    Returns:
        Normalized path string.
    """
    path = PurePosixPath(file_name)

    # Reject absolute paths
    if path.is_absolute():
        raise HTTPException(status_code=400, detail="...")

    # Reject path traversal segments
    if ".." in path.parts:
        raise HTTPException(status_code=400, detail="...")

    # Normalize and return (removes . segments)
    # Note: PurePosixPath doesn't normalize ./ but we can handle it
    normalized = "/".join(p for p in path.parts if p != ".")
    return normalized or file_name
```

## Tasks

- [ ] 絶対パス拒否の実装
- [ ] パス正規化の実装
- [ ] バリデーション結果を返すように関数を変更
- [ ] 重複チェックに正規化されたパスを使用
- [ ] テスト追加
- [ ] Commit
- [ ] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [ ] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Update docs/architecture/*.md
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## Notes

- codex MCP レビューで指摘された Medium severity 問題
- 260130-filepath-handling-improvements から派生
