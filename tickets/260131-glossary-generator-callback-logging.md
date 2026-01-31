---
priority: 1
tags: [improvement, debugging]
description: "GlossaryGenerator: Add logging to _safe_callback for debugging"
created_at: "2026-01-31T02:15:00Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# GlossaryGenerator: Add logging to _safe_callback for debugging

## 概要

codex MCPのレビューにより、`_safe_callback` メソッドがエラーをログなしで抑制しているため、デバッグが困難であることが指摘された。

## 問題点

**現在のコード (src/genglossary/glossary_generator.py:62)**:
```python
def _safe_callback(
    self, callback: Callable[..., None] | None, *args: Any
) -> None:
    """Safely invoke a callback, ignoring any exceptions."""
    if callback is not None:
        try:
            callback(*args)
        except Exception:
            pass  # Ignore callback errors to prevent pipeline interruption
```

- コールバックエラーが完全に無視される
- デバッグ時にプログレスフックの問題を特定するのが困難

## 改善案

1. `logger.debug()` でエラーをログする
2. オプションでstrict modeを提供する（エラーを伝播させる）

```python
def _safe_callback(
    self, callback: Callable[..., None] | None, *args: Any
) -> None:
    if callback is not None:
        try:
            callback(*args)
        except Exception as e:
            logger.debug(
                "Callback error ignored (to prevent pipeline interruption): %s",
                e,
                exc_info=True,
            )
```

## Tasks

- [ ] テストケースの作成
- [ ] ログ追加の実装
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## 関連

- 元チケット: 260130-glossary-generator-code-simplification
- codex MCPレビュー結果
