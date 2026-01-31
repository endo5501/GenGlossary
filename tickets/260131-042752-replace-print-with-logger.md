---
priority: 3
tags: [refactoring, code-quality, backend, logging]
description: "Replace print statements with logger.warning for consistent logging"
created_at: "2026-01-31T04:27:52Z"
started_at: null  # Do not modify manually
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

- [ ] `glossary_refiner.py` の `print` を `logger.warning` に置き換え
- [ ] `glossary_reviewer.py` の `print` を `logger.warning` に置き換え
- [ ] 他のファイルで同様の問題がないか確認
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

- code-simplifier agent レビューで指摘（260131-safe-callback-extraction チケット作業中）
