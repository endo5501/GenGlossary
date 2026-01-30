---
priority: 3
tags: [improvement, backend, executor, refactoring]
description: "PipelineExecutor: Reduce duplicated cancellation check pattern"
created_at: "2026-01-30T20:50:00Z"
started_at: null
closed_at: null
---

# PipelineExecutor: Reduce duplicated cancellation check pattern

## 概要

各ステップ前で繰り返される `if self._check_cancellation(): return` パターンを DRY 原則に従って統一する。

## 現状の問題

**問題箇所**: `executor.py` 全体で10箇所

```python
if self._check_cancellation():
    return
```

このパターンが各ステップの前で繰り返されており、冗長。

## 提案する解決策

### オプション1: デコレータパターン

```python
def cancellable(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if self._check_cancellation():
            return
        return func(self, *args, **kwargs)
    return wrapper

@cancellable
def _execute_full(self, conn, doc_root):
    ...
```

### オプション2: ステップ実行ヘルパー

```python
def _run_step(self, step_func, *args, **kwargs):
    if self._check_cancellation():
        return False
    step_func(*args, **kwargs)
    return True
```

## 影響範囲

- `src/genglossary/runs/executor.py`

## Tasks

- [ ] 設計選択
- [ ] 実装
- [ ] テスト更新
- [ ] Commit
- [ ] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest`) before reviwing and pass all tests (No exceptions)
- [ ] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket.
- [ ] Code review by codex MCP. If the issue is not addressed immediately, create a ticket.
- [ ] Update docs/architecture/*.md
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## Notes

- code-simplifier レビューで指摘
- 優先度低：機能的には問題なし、保守性の改善
