---
priority: 6
tags: [refactoring, backend, code-quality]
description: "RunManager: Refactor duplicated status update code"
created_at: "2026-01-31T10:10:00+09:00"
started_at: null
closed_at: null
---

# RunManager: Refactor duplicated status update code

## 概要

code-simplifier agent レビューで指摘された問題。ステータス更新処理に重複コードがあり、リファクタリングにより保守性を向上できる。

## 重複コードの詳細

### 1. フォールバック処理パターンの重複

`_finalize_run_status` メソッドで、キャンセル処理と完了処理で同じフォールバックパターンが重複：

```python
# キャンセルの場合
if not self._try_cancel_status(conn, run_id):
    try:
        with database_connection(self.db_path) as fallback_conn:
            self._try_cancel_status(fallback_conn, run_id)
    except Exception as e:
        self._broadcast_log(run_id, {...warning...})

# 完了の場合（同じパターン）
if not self._try_complete_status(conn, run_id):
    ...
```

### 2. 3つの `_try_*_status` メソッドの構造重複

- `_try_cancel_status`
- `_try_complete_status`
- `_try_update_status`

これらのメソッドは同じ構造を持ち、パラメータ化により統合可能。

## 提案される改善

### 汎用フォールバック処理メソッド

```python
def _try_status_with_fallback(
    self,
    conn: sqlite3.Connection,
    run_id: int,
    status_updater: Callable[[sqlite3.Connection, int], bool],
    operation_name: str
) -> None:
    """Try status update with fallback to new connection."""
    if not status_updater(conn, run_id):
        try:
            with database_connection(self.db_path) as fallback_conn:
                status_updater(fallback_conn, run_id)
        except Exception as e:
            self._broadcast_log(
                run_id,
                {
                    "run_id": run_id,
                    "level": "warning",
                    "message": f"Failed to update {operation_name} status: {e}",
                },
            )
```

### 予想される効果

- 約50-60行のコード削減
- 新しいステータス遷移追加時の変更箇所最小化
- 保守性と可読性の向上

## 関連ファイル

- `src/genglossary/runs/manager.py`

## Tasks

- [ ] 汎用ステータス更新メソッドの設計
- [ ] リファクタリング実施
- [ ] テストが引き続きパスすることを確認
