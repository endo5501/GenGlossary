---
priority: 9
tags: [improvement, backend, executor, refactoring]
description: "PipelineExecutor: Simplify _log method using dict comprehension"
created_at: "2026-01-30T20:50:00Z"
started_at: null
closed_at: null
---

# PipelineExecutor: Simplify _log method

## 概要

`_log` メソッド内の繰り返し条件分岐を辞書内包表記で簡素化する。

## 現状の問題

**問題箇所**: `executor.py:79-92`

```python
log_entry: dict = {"run_id": self._run_id, "level": level, "message": message}
if step is not None:
    log_entry["step"] = step
if current is not None:
    log_entry["progress_current"] = current
if total is not None:
    log_entry["progress_total"] = total
if current_term is not None:
    log_entry["current_term"] = current_term
```

5つのオプショナルパラメータそれぞれに条件分岐があり、冗長。

## 提案する解決策

```python
log_entry = {
    "run_id": self._run_id,
    "level": level,
    "message": message,
    **{k: v for k, v in {
        "step": step,
        "progress_current": current,
        "progress_total": total,
        "current_term": current_term
    }.items() if v is not None}
}
```

## 影響範囲

- `src/genglossary/runs/executor.py`

## Tasks

- [ ] 実装
- [ ] テスト確認

## Notes

- code-simplifier レビューで指摘
- 優先度低：可読性の好みの問題
