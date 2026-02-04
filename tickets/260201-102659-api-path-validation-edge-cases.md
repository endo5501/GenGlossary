---
priority: 1
tags: [improvement, backend]
description: "API path validation: handle edge cases (empty segments, length limits)"
created_at: "2026-02-01T10:26:59Z"
started_at: 2026-02-04T12:57:38Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# API path validation: handle edge cases

## 概要

codex MCP レビューで指摘された追加のエッジケース。

## 問題点

### 1. 空セグメント
- `a//b.md` が許可されており、`a/b.md` とは別として扱われる
- ファイルシステムでは同じパスに正規化される可能性

### 2. パス長制限なし
- 非常に長いファイル名が保存可能
- ファイルシステムの制限（255バイト/セグメント）を超える可能性

### 3. bulk create の IntegrityError
- 事前チェック後にレース条件で重複が発生した場合、500エラーになる
- 409を返すべき

## 推奨修正

1. 空セグメントを拒否または正規化
2. パス長制限を追加（例: セグメント255バイト、全体1024バイト）
3. bulk create に try/except 追加

## 影響箇所

- `src/genglossary/api/routers/files.py`

## Tasks

- [ ] 空セグメント対応
- [ ] パス長制限追加
- [ ] bulk create の IntegrityError 対応
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

- 260201-084114-api-path-validation-enhancement の codex レビューで指摘
- ケース感度の問題はmacOS/Windowsで影響するが、DB層での対応が必要なため別途検討
