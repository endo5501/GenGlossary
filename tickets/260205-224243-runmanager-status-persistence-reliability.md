---
priority: 2
tags: [backend, bug-prevention]
description: "Improve RunManager status persistence reliability"
created_at: "2026-02-05T22:42:43Z"
started_at: 2026-02-05T22:48:27Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# Improve RunManager status persistence reliability

## Overview

Codex review identified potential reliability issues with status persistence in RunManager:

1. **Silent failure**: Status updates can fail silently, leaving runs stuck in `pending`/`running` while subscribers get a completion signal
2. **UI/DB state mismatch**: `_cleanup_run_resources` always broadcasts `complete` regardless of DB state

## Related Files

- `src/genglossary/runs/manager.py:342` (`_cleanup_run_resources`)
- `src/genglossary/runs/manager.py:364` (`_try_status_with_fallback`)
- `src/genglossary/runs/manager.py:512` (`_update_failed_status`)

## Current Behavior

```python
def _try_status_with_fallback(...):
    # If both primary and fallback updates fail, only logs a warning
    # No retry, no exponential backoff

def _cleanup_run_resources(self, run_id):
    # Always broadcasts complete signal, even if DB update failed
    self._broadcast_log(run_id, {"run_id": run_id, "complete": True})
```

## Problems

1. Run can remain "active" in DB indefinitely if both update attempts fail
2. UI shows "completed" while DB still shows "running"
3. No retry/backoff mechanism for transient DB failures
4. `print` statements in background threads can interleave

## Proposed Solutions

### Option A: Enhanced logging and alerts
- Add structured logging instead of `print`
- Add metric/alert when status update fails

### Option B: Retry with backoff
- Add retry logic with exponential backoff for status updates
- Configurable max retries and base delay

### Option C: Include DB state in completion signal
- Modify completion signal to include actual DB status
- UI can show warning if status update failed

## Tasks

- [x] Analyze current failure modes and their impact
- [x] Choose solution approach
- [x] Implement chosen solution
- [x] Replace `print` with structured logging
- [x] Add tests for failure scenarios
- [x] Commit
- [ ] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Update docs/architecture/*.md
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## Design (Approved)

### Approach
- **Option A + C の組み合わせ**: ログ出力の充実 + 完了シグナルへのDB状態追加
- リトライ機構は現時点では不要

### Changes

| 項目 | 変更 |
|-----|------|
| ロギング導入 | `logging.getLogger(__name__)` を追加、`print`文を`logger.error(..., exc_info=True)`に置換 |
| `_cleanup_run_resources` | `db_status`, `status_update_failed` パラメータを追加 |
| `_try_status_with_fallback` | 戻り値`bool`を追加（成功/失敗を返す） |
| `_finalize_run_status` | 戻り値`tuple[str, bool]`を追加（ステータスと成功フラグ） |
| `_update_failed_status` | 戻り値`bool`を追加 |
| `_execute_run` | 最終ステータスを追跡し`_cleanup_run_resources`に渡す |
| `start_run` | 例外時に`db_status="failed"`を渡す |

### Completion Signal Format
- 成功時: `{"run_id": 1, "complete": True, "db_status": "completed"}`
- DB更新失敗時: `{"run_id": 1, "complete": True, "db_status": "failed", "status_update_failed": True}`

## Notes

Identified by codex MCP during review of ticket 260205-132314.
Priority 2 due to potential for user-facing inconsistency.
