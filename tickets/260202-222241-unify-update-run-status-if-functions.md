---
priority: 3
tags: [backend, db, refactoring]
description: "Refactor: unify update_run_status_if_* functions with common helper"
created_at: "2026-02-02T22:22:41Z"
started_at: 2026-02-05T15:39:40Z # Do not modify manually
closed_at: 2026-02-05T15:45:53Z # Do not modify manually
---

# Refactor: unify update_run_status_if_* functions with common helper

## 概要

`update_run_status_if_active` と `update_run_status_if_running` の間に顕著なコード重複がある。
共通の内部ヘルパー関数 `_update_run_status_if_in_states` を導入することで、重複を削減し保守性を向上させる。

## 背景

code-simplifier agent による分析で、以下の重複が指摘された：
- `finished_at` のデフォルト処理ロジック
- SQL UPDATE文の構造
- `rowcount` チェックとコミットロジック

## 提案された実装

```python
def _update_run_status_if_in_states(
    conn: sqlite3.Connection,
    run_id: int,
    status: str,
    allowed_states: tuple[str, ...],
    error_message: str | None = None,
    finished_at: datetime | None = None,
) -> int:
    """Update run status only if current status is in allowed_states.

    Internal helper function to reduce duplication.
    """
    # 共通ロジックをここに集約
    ...

def update_run_status_if_active(...) -> int:
    return _update_run_status_if_in_states(
        conn, run_id, status, ('pending', 'running'), error_message, finished_at
    )

def update_run_status_if_running(...) -> int:
    return _update_run_status_if_in_states(
        conn, run_id, status, ('running',), None, finished_at
    )
```

## 期待される効果

- 約40行のコード削減
- ロジック変更が1箇所で済む
- 将来、他の状態チェックが必要になった場合も簡単に対応可能

## Tasks

- [x] `_update_run_status_if_in_states` 内部ヘルパー関数を実装
- [x] `update_run_status_if_active` をヘルパー関数を使うよう変更
- [x] `update_run_status_if_running` をヘルパー関数を使うよう変更
- [x] 既存テストが全てパスすることを確認
- [x] Commit
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Update docs/architecture/*.md (N/A - internal helper function)
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing

## Notes

この変更により、機能を一切変更せずにコードの保守性と可読性が向上する。
既存のテストがそのまま動作することを確認することが重要。
