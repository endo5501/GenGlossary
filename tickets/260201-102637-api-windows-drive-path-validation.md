---
priority: 5
tags: [security, backend]
description: "API path validation: reject Windows drive paths"
created_at: "2026-02-01T10:26:37Z"
started_at: 2026-02-01T11:32:50Z # Do not modify manually
closed_at: 2026-02-01T11:41:22Z # Do not modify manually
---

# API path validation: reject Windows drive paths

## 概要

codex MCP レビューで指摘された問題。`C:/Windows/system32/...` のようなWindows形式の絶対パスが検証をすり抜ける。

## 問題点

- `_validate_file_name` は `/` で始まるパスのみを絶対パスとして拒否
- `C:/path/to/file.md` は `/` で始まらず、バックスラッシュも使っていないためパス
- Windows環境で `Path(base, name)` を使用すると、ドライブ付きパスはbaseを無視

## 推奨修正

ドライブレター + コロン（`^[A-Za-z]:`）を拒否する。

## 影響箇所

- `src/genglossary/api/routers/files.py:_validate_file_name`

## Tasks

- [x] ドライブレター形式の拒否を実装
- [x] テスト追加
- [x] Commit
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Update docs/architecture/*.md
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing

## Notes

- 260201-084114-api-path-validation-enhancement の codex レビューで指摘
- codex レビューから派生チケット作成: 260201-113740-api-path-unicode-normalization
