---
priority: 2
tags: [improvement, backend, security]
description: "Sanitize error messages before DB persistence and API exposure"
created_at: "2026-02-08T09:44:48Z"
started_at: 2026-02-08T10:37:58Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# Sanitize error messages before DB persistence and API exposure

## 概要

Codex MCPレビューで指摘。RunManagerの `error_message` フィールドには生の例外テキストが保存され、APIレスポンスとしてそのまま返される（`run_schemas.py:37`）。ファイルシステムパス、ホスト名等の機密情報が漏洩するリスクがある。

## 現状の問題

- `runs.error_message` は `TEXT` 型で長さ制限なし（`schema.py:111`）
- 例外の `str(e)` がそのままDBに保存される
- APIレスポンスでそのまま返される
- `str(e)` が空の場合、末尾にコロンが残る不自然なメッセージになる

## 承認済み設計

### モジュール構成

新規ファイル `src/genglossary/runs/error_sanitizer.py` を作成。

関数 `sanitize_error_message(error, prefix=None, max_length=1024) -> str`

### サニタイズ処理（順に適用）

1. **空メッセージのフォールバック**: `str(e)` が空なら例外クラス名を使用
2. **非UTF-8文字の正規化**: `msg.encode("utf-8", "replace").decode("utf-8")`
3. **制御文字の除去**: 改行・タブ以外の制御文字を除去
4. **機密パスのマスキング**: Unix/Windowsの2セグメント以上のパスを `<path>` に置換（URLは除外）
5. **長さ制限**: 1024文字で切り詰め、超過時は `"...(truncated)"` を付加

### 出力フォーマット

- prefix あり + メッセージあり: `"{prefix}: {sanitized_msg} ({ExceptionClass})"`
- prefix あり + メッセージ空: `"{prefix} ({ExceptionClass})"`
- prefix なし + メッセージあり: `"{sanitized_msg} ({ExceptionClass})"`
- prefix なし + メッセージ空: `"{ExceptionClass}"`

### manager.py 変更箇所（3箇所）

1. L122: スレッド起動失敗時 — `sanitize_error_message(e, "Failed to start execution thread")`
2. L232: パイプライン外エラー — `sanitize_error_message(e)`
3. L468: パイプラインエラー — `sanitize_error_message(pipeline_error)`

## Tasks

- [x] 設計レビュー・承認
- [ ] 実装
- [ ] テストの更新
- [ ] Commit
- [ ] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [ ] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Update docs (glob: "*.md" in ./docs/architecture)
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## Notes

- 260202-225133チケットのcodex MCPレビューで指摘
- 関連ファイル: `src/genglossary/runs/manager.py`, `src/genglossary/api/schemas/run_schemas.py`, `src/genglossary/db/schema.py`
