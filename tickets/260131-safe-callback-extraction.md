---
priority: 1
tags: [refactoring, code-quality, backend]
description: "Extract _safe_callback to common utility module"
created_at: "2026-01-31T04:10:00Z"
started_at: 2026-01-31T04:20:22Z
closed_at: null
---

# Extract _safe_callback to common utility module

## 概要

`_safe_callback` メソッドが `glossary_generator.py` と `glossary_refiner.py` で完全に重複している。DRY原則に従い、共通ユーティリティモジュールに抽出すべき。

## 現状

- `glossary_generator.py` の `GlossaryGenerator._safe_callback`
- `glossary_refiner.py` の `GlossaryRefiner._safe_callback`

両方とも同一のコード:
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

## 提案

`src/genglossary/utils/callback.py` に抽出:

```python
def safe_callback(callback: Callable[..., None] | None, *args: Any) -> None:
    """Safely invoke a callback, ignoring any exceptions."""
    ...
```

## Tasks

- [ ] `src/genglossary/utils/callback.py` を作成
- [ ] テストを追加
- [ ] `glossary_generator.py` を更新
- [ ] `glossary_refiner.py` を更新
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

- code-simplifier agent レビューで指摘
- 緊急性は低い
