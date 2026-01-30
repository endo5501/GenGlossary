---
priority: 7
tags: [refactoring, code-quality, backend]
description: "Backend: Progress callback code refactoring"
created_at: "2026-01-30T09:45:00Z"
started_at: null
closed_at: null
---

# Backend: Progress callback code refactoring

## 概要

Backend のプログレスコールバック関連コードの小規模リファクタリング。

## 対応項目

### 1. 重複したコールバック処理パターンの共通化
- 場所: `glossary_generator.py`, `glossary_refiner.py`
- 両方で同じ try-except パターンが繰り返されている
- 共通ヘルパー関数 `invoke_progress_callbacks()` への抽出

### 2. `_log` メソッドの簡略化
- 場所: `executor.py`
- 辞書内包表記を使用してより簡潔に書ける

### 3. `_log` の run_id=None 処理
- `execute` が run_id なしで呼ばれると `run_id: None` がログに含まれる
- `run_id is None` の場合はフィールドを省略する

### 4. 空の term_name メッセージフォーマット
- `term_name=""` の場合、`: 0%` というメッセージになる
- フォールバックラベルを使用するか、`current_term` を省略する

## Tasks

- [ ] テストを追加・更新
- [ ] 重複したコールバック処理パターンの共通化実装
- [ ] `_log` メソッドの簡略化
- [ ] `_log` の run_id=None 処理
- [ ] 空の term_name メッセージフォーマット
- [ ] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [ ] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket.
- [ ] Code review by codex MCP. If the issue is not addressed immediately, create a ticket.
- [ ] Update docs/architecture/*.md
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## Notes

- 機能には影響しないコード品質改善
- 緊急性は低い
