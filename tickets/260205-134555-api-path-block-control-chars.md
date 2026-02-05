---
priority: 2
tags: [security, backend]
description: "API path validation: block control characters, bidi overrides, and Windows reserved names"
created_at: "2026-02-05T13:45:55Z"
started_at: 2026-02-05T15:19:55Z # Do not modify manually
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

- [x] 制御文字のチェックを追加
- [x] 双方向上書き文字/ゼロ幅文字のチェックを追加
- [x] look-alike 文字リストを拡張
- [x] Unicode 空白文字の末尾チェックを追加
- [x] Windows 予約デバイス名をブロック
- [x] テスト追加
- [x] Commit
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Update docs/architecture/*.md
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## Design

### 設計方針

- **エラーメッセージ**: 統一メッセージ（"File name contains disallowed Unicode characters"）でセキュリティ情報を露出しない
- **Windows予約名チェック**: ベースネーム（ファイル名）のみ。ディレクトリ名は許可

### 追加する定数

```python
# 既存の LOOKALIKE_DOT に追加
LOOKALIKE_DOT_ADDITIONAL = {"\u3002", "\uff61"}  # 。 ｡ (CJKの句点)

# 制御文字（C0/C1）
CONTROL_CHARS = set(chr(c) for c in range(0x00, 0x20)) | set(chr(c) for c in range(0x7F, 0xA0))

# 双方向上書き文字・ゼロ幅文字
BIDI_AND_ZERO_WIDTH = {"\u200b", "\u200c", "\u200d", "\u200e", "\u200f",
                       "\u202a", "\u202b", "\u202c", "\u202d", "\u202e", "\ufeff"}

# Unicode空白文字（末尾チェック用）
UNICODE_WHITESPACE = {"\u00a0", "\u2000", "\u2001", "\u2002", "\u2003", "\u2009", "\u200a", "\u3000"}

# Windows予約デバイス名
WINDOWS_RESERVED_NAMES = {"CON", "PRN", "AUX", "NUL"} | {f"COM{i}" for i in range(1, 10)} | {f"LPT{i}" for i in range(1, 10)}
```

### チェック追加位置

1. NFC正規化直後: 制御文字、双方向/ゼロ幅文字、look-alike文字
2. セグメントループ内: Unicode空白末尾チェック（既存チェックを拡張）
3. 拡張子チェック前: Windows予約デバイス名

### テストケース（13件）

- 制御文字: NUL, 改行, C1制御文字
- 双方向/ゼロ幅: RTL override, ZWSP, ZWJ
- look-alike拡張: CJK fullstop, halfwidth fullstop
- Unicode空白末尾: NBSP, 全角空白
- Windows予約名: CON, COM1（拒否）、ディレクトリ内CON、部分文字列（許可）

## Notes

- 260201-113740-api-path-unicode-normalization の codex レビューで指摘
