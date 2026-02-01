---
priority: 1
tags: [backend, refactoring]
description: "runs_repository: Extract helper functions for timestamp handling"
created_at: "2026-02-01T00:24:56Z"
started_at: 2026-02-01T06:05:13Z # Do not modify manually
closed_at: 2026-02-01T06:15:59Z # Do not modify manually
---

# runs_repository: Extract helper functions for timestamp handling

## 概要

runs_repository.py のタイムスタンプ処理ロジックを共通のヘルパー関数に抽出し、コードの重複を削減する。

## 改善内容

### 1. _to_iso_string ヘルパー関数の作成

タイムゾーン検証と ISO 文字列変換を統一する関数を作成。

```python
def _to_iso_string(dt: datetime | None, param_name: str) -> str | None:
    """Convert timezone-aware datetime to ISO string."""
    if dt is None:
        return None
    _validate_timezone_aware(dt, param_name)
    return dt.isoformat(timespec="seconds")
```

### 2. _current_utc_iso ヘルパー関数の作成

現在の UTC 時刻を ISO 文字列で取得する関数を作成。

```python
def _current_utc_iso() -> str:
    """Get current UTC time as ISO string."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
```

### 対象箇所

- `create_run` 関数
- `update_run_status` 関数
- `update_run_status_if_active` 関数

## Tasks

- [x] Add _to_iso_string helper function
- [x] Add _current_utc_iso helper function
- [x] Refactor create_run to use helpers
- [x] Refactor update_run_status to use helpers
- [x] Refactor update_run_status_if_active to use helpers
- [x] Add tests
- [x] Commit
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Update docs/architecture/*.md
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing

## Notes

- Source: code-simplifier review from ticket 260201-001229-additional-timestamp-improvements
