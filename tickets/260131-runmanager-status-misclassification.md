---
priority: 2
tags: [bug, backend, reliability]
description: "RunManager: Fix status misclassification on DB update failure"
created_at: "2026-01-31T15:20:00+09:00"
started_at: null
closed_at: null
---

# RunManager: Fix status misclassification on DB update failure

## 概要

`_execute_run` メソッドで、パイプライン実行後のDB更新で例外が発生した場合、成功またはキャンセルされたrunが誤って `failed` としてマークされる問題。

## codex MCP レビューからの指摘

**場所**: `src/genglossary/runs/manager.py:137-150`

`executor.execute()` 後の例外（`cancel_run` や `complete_run_if_not_cancelled` 内の一時的なDBエラーを含む）がすべてキャッチされ、`_update_failed_status` が呼ばれるため、実際には成功またはキャンセルされたrunが `failed` としてマークされる可能性がある。

### 問題のシナリオ

1. パイプライン実行が正常に完了
2. `complete_run_if_not_cancelled` でDB更新時に一時的なエラー（例: "database is locked"）
3. 例外がキャッチされ、runが `failed` としてマークされる
4. 実際にはパイプラインは成功していたのに、ステータスが誤っている

### キャンセル時の問題

1. ユーザーがキャンセルをリクエスト
2. `cancel_event.is_set()` が true
3. `cancel_run(conn, run_id)` でDB更新時にエラー
4. 例外がキャッチされ、runが `failed` としてマークされる
5. ユーザーには `cancelled` ではなく `failed` と表示される

## 提案される解決策

1. パイプライン実行と最終ステータス更新を別々の try/except でラップ
2. ステータス更新失敗時は、新しい接続でリトライ
3. `cancel_event.is_set()` の場合は、`failed` ではなく `cancelled` を優先

```python
def _execute_run(self, run_id: int, scope: str) -> None:
    conn = None
    pipeline_error = None

    try:
        conn = get_connection(self.db_path)
        # ... running status update ...

        try:
            executor.execute(conn, scope, context, doc_root=self.doc_root)
        except Exception as e:
            pipeline_error = e

        # パイプライン完了後のステータス更新
        self._finalize_run_status(conn, run_id, cancel_event, pipeline_error)

    except Exception as e:
        # 接続エラーなど、パイプライン外のエラー
        self._update_failed_status(conn, run_id, str(e))
    finally:
        # cleanup...
```

## 影響範囲

- `src/genglossary/runs/manager.py`

## Tasks

- [ ] パイプライン実行と最終ステータス更新の例外処理を分離
- [ ] キャンセル時のステータス更新失敗時に `cancelled` を優先するロジック追加
- [ ] テストの追加
- [ ] Commit
- [ ] Run static analysis (`pyright`) before reviewing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest`) before reviewing and pass all tests (No exceptions)
- [ ] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket.
- [ ] Code review by codex MCP. If the issue is not addressed immediately, create a ticket.
- [ ] Update docs/architecture/*.md
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing
