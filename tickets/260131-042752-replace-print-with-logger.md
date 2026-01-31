---
priority: 3
tags: [refactoring, code-quality, backend, logging]
description: "Replace print statements with logger.warning for consistent logging"
created_at: "2026-01-31T04:27:52Z"
started_at: 2026-01-31T14:03:33Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# Replace print statements with logger.warning

## 概要

一部のモジュールで警告メッセージに `print` 文を使用しているが、モジュールには既に `logger` が定義されている。ログ戦略の統一のため `logger.warning` に置き換える。

## 対象箇所

### glossary_refiner.py (110行目)

```python
# Before
print(f"Warning: Failed to refine '{issue.term_name}': {e}")

# After
logger.warning(
    "Failed to refine '%s': %s",
    issue.term_name,
    e,
    exc_info=True,
)
```

### glossary_reviewer.py (62行目)

```python
# Before
print(f"Warning: Failed to review glossary: {e}")

# After
logger.warning("Failed to review glossary: %s", e, exc_info=True)
```

## 問題点

- モジュールの先頭で `logger` が定義されているのに `print` を使用
- ログレベルの制御ができない
- 構造化されたログ記録の利点を活用できていない

## Tasks

- [x] `glossary_refiner.py` の `print` を `logger.warning` に置き換え
- [x] `glossary_reviewer.py` の `print` を `logger.warning` に置き換え
- [x] 他のファイルで同様の問題がないか確認
- [x] Commit
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Update docs/architecture/*.md (不要 - アーキテクチャ変更なし)
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing

## Notes

- code-simplifier agent レビューで指摘（260131-safe-callback-extraction チケット作業中）

## 完了サマリー

### 変更内容
- `glossary_refiner.py`: `print` → `logger.warning` (exc_info=True)
- `glossary_reviewer.py`: `logging` インポート追加、`logger` 定義追加、`print` → `logger.warning`

### コミット
- f116885: Add tests for logger.warning usage
- 6d67259: Replace print statements with logger.warning
- e594ee0: Fix logger placement per PEP8 import ordering

### レビュー結果
- code-simplifier: 問題なし
- codex MCP: PEP8スタイル指摘 → 修正済み
