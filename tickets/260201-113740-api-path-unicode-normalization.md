---
priority: 2
tags: [security, backend]
description: "API path validation: Unicode normalization and edge cases"
created_at: "2026-02-01T11:37:40Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# API path validation: Unicode normalization and edge cases

## 概要

codex MCP レビューで指摘された追加のセキュリティ問題。パス検証におけるUnicode正規化とエッジケースの対応。

## 問題点

- Unicode look-alike文字（U+2215, U+FF0F, U+2024など）でセパレータやドットを偽装可能
- 末尾のスペースやドット（Windows特有の問題）
- NFC正規化が行われていない

## 推奨修正

1. NFC正規化を適用
2. Unicode look-alike セパレータを拒否
3. 末尾のスペース/ドットを拒否

## 影響箇所

- `src/genglossary/api/routers/files.py:_validate_file_name`

## Tasks

- [ ] Unicode正規化（NFC）を実装
- [ ] Unicode look-alike文字のチェックを追加
- [ ] 末尾スペース/ドットのチェックを追加
- [ ] テスト追加
- [ ] Commit
- [ ] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest`) before reviwing and pass all tests (No exceptions)
- [ ] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Update docs/architecture/*.md
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## Notes

- 260201-102637-api-windows-drive-path-validation の codex レビューで指摘
