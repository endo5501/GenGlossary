---
priority: 4
tags: [improvement, backend, executor, refactoring]
description: "PipelineExecutor: Simplify _log method using dict comprehension"
created_at: "2026-01-30T20:50:00Z"
started_at: 2026-02-01T08:05:40Z
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

- [x] 実装（既に完了済み）
- [x] テスト確認
- [x] Commit（既存のコミットで完了）
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Update docs/architecture/*.md（変更不要）
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing

## Notes

- code-simplifier レビューで指摘
- 優先度低：可読性の好みの問題
