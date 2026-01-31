---
priority: 2
tags: [refactoring, code-quality, backend]
description: "TermExtractor: Use safe_callback for callback consistency"
created_at: "2026-01-31T04:27:21Z"
started_at: 2026-01-31T04:48:42Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# TermExtractor: Use safe_callback for callback consistency

## 概要

`TermExtractor` クラスでコールバック呼び出しが `safe_callback` ユーティリティを使用していないため、コールバックで例外が発生した場合にパイプライン処理が中断される。

## 現状

`term_extractor.py` の501-502行目:

```python
if progress_callback is not None:
    progress_callback(batch_num, total_batches)
```

## 問題点

- コールバックで例外が発生した場合、パイプライン処理が中断される
- エラーハンドリングの一貫性がない（他のクラスは`safe_callback`を使用）

## 提案

```python
# Before
if progress_callback is not None:
    progress_callback(batch_num, total_batches)

# After
from genglossary.utils.callback import safe_callback
safe_callback(progress_callback, batch_num, total_batches)
```

## Tasks

- [x] `term_extractor.py` を更新して `safe_callback` を使用
- [x] テストを追加（コールバック例外時の継続確認）
- [x] Commit
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Update docs/architecture/*.md (N/A: docs/architecture/ directory does not exist)
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing

## Notes

- code-simplifier agent レビューで指摘（260131-safe-callback-extraction チケット作業中）
- `GlossaryGenerator` と `GlossaryRefiner` との一貫性向上のため
