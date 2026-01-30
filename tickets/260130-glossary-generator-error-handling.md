---
priority: 5
tags: [improvement, code-quality]
description: "GlossaryGenerator: print()をloggingに置き換え"
created_at: "2026-01-30T08:20:00Z"
started_at: 2026-01-30T09:48:56Z # Do not modify manually
closed_at: 2026-01-30T10:01:46Z # Do not modify manually
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

- [x] エラーハンドリング方式の決定（logging vs callback vs 両方） → **案1: loggingを採用**
- [x] 実装
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket.
  - → 別チケット作成: `260130-glossary-generator-code-simplification.md`
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket.
  - → プロンプトインジェクション対策は既存チケット `260130-glossary-generator-prompt-security.md` で対応
- [x] Update docs/architecture/*.md → **不要**（APIに影響なし）
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing

## 実装内容

### コミット履歴
- `d2269ea` Add tests for logging warning on definition generation failure
- `80d74cb` Replace print() with logging.warning() in GlossaryGenerator
- `62c204e` Add exc_info=True to warning log for stack trace
- `2984ec7` Add ticket for GlossaryGenerator code simplification

### 変更ファイル
- `src/genglossary/glossary_generator.py`: `print()` → `logger.warning()` with `exc_info=True`
- `tests/test_glossary_generator.py`: `TestGlossaryGeneratorErrorLogging` クラス追加（3テスト）

### テスト結果
- Python: 720 passed
- pyright: 0 errors
- Frontend: 152 passed

## 関連

- 元チケット: 260129-155649-glossary-generator-prompt-refactoring
- 派生チケット: 260130-glossary-generator-code-simplification
