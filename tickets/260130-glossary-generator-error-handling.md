---
priority: 5
tags: [improvement, code-quality]
description: "GlossaryGenerator: print()をloggingに置き換え"
created_at: "2026-01-30T08:20:00Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# GlossaryGenerator: print()をloggingに置き換え

## 概要

code-simplifier agentおよびcodex MCPレビューにより、`glossary_generator.py`のエラーハンドリング改善が推奨された。

## 現状の問題

- `generate`メソッドで例外発生時に`print()`を使用している（113-116行目）
- テストが困難
- ログレベルの制御ができない
- 出力先の制御ができない

## 改善案

### 案1: loggingを使用
```python
import logging

logger = logging.getLogger(__name__)

# In except block
except Exception as e:
    logger.warning(
        "Failed to generate definition for '%s': %s",
        term_name,
        e,
        exc_info=True
    )
    continue
```

### 案2: エラーコールバックを追加
```python
def generate(
    self,
    ...,
    error_callback: ErrorCallback | None = None,
) -> Glossary:
    # ...
    except Exception as e:
        if error_callback is not None:
            error_callback(term_name, e)
        continue
```

## Tasks

- [ ] エラーハンドリング方式の決定（logging vs callback vs 両方）
- [ ] 実装
- [ ] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [ ] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket.
- [ ] Code review by codex MCP. If the issue is not addressed immediately, create a ticket.
- [ ] Update docs/architecture/*.md
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## 関連

- 元チケット: 260129-155649-glossary-generator-prompt-refactoring
