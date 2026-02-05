---
priority: 2
tags: [security, backend]
description: "API path validation: block control characters, bidi overrides, and Windows reserved names"
created_at: "2026-02-05T13:45:55Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# API path validation: block control characters and enhance security

## 概要

codex MCP レビューで指摘された追加のセキュリティ問題。260201-113740-api-path-unicode-normalization の継続。

## 問題点

- 制御文字（C0/C1 controls, NUL）が許可されている
- 双方向上書き文字（U+202E）やゼロ幅文字（U+200B/U+200D）でファイル名の偽装が可能
- look-alike 文字リストが不完全（U+3002, U+FF61 などの追加ドット類似文字）
- 末尾空白チェックがASCIIのみ（U+00A0 などの Unicode 空白が許可されている）
- Windows 予約デバイス名（CON, PRN, AUX, NUL, COM1, LPT1）が未ブロック

## 推奨修正

1. 制御文字（U+0000-U+001F, U+007F-U+009F）を拒否
2. 双方向上書き文字とゼロ幅文字を拒否
3. look-alike 文字リストを拡張
4. Unicode 空白文字の末尾チェックを追加
5. Windows 予約デバイス名をブロック

## 影響箇所

- `src/genglossary/api/routers/files.py:_validate_file_name`

## Tasks

- [ ] 制御文字のチェックを追加
- [ ] 双方向上書き文字/ゼロ幅文字のチェックを追加
- [ ] look-alike 文字リストを拡張
- [ ] Unicode 空白文字の末尾チェックを追加
- [ ] Windows 予約デバイス名をブロック
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

- 260201-113740-api-path-unicode-normalization の codex レビューで指摘
