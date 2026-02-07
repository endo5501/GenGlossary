---
priority: 3
tags: [security, backend]
description: "Block Windows-invalid characters in file paths"
created_at: "2026-02-05T15:34:44Z"
started_at: 2026-02-07T06:23:13Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# Block Windows-invalid characters in file paths

## 概要

codex MCP レビューで指摘された追加のセキュリティ問題。260205-134555-api-path-block-control-chars の継続。

## 問題点

- Windows/NTFS で問題となる文字（`:`, `<`, `>`, `"`, `|`, `?`, `*`）が許可されている
- `:` は NTFS の Alternate Data Stream (ADS) を作成する可能性がある

## 推奨修正

1. Windows 不正文字セットを定義してブロック
2. ADS パターン (`file.txt:stream`) を拒否

## 影響箇所

- `src/genglossary/api/routers/files.py:_validate_file_name`

## Tasks

- [x] Windows 不正文字のチェックを追加
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

- 260205-134555-api-path-block-control-chars の codex レビューで指摘
