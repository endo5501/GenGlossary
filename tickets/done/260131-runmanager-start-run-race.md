---
priority: 4
tags: [improvement, backend, reliability]
description: "RunManager: Prevent race condition in start_run"
created_at: "2026-01-31T15:20:00+09:00"
started_at: 2026-02-01T10:17:00Z
closed_at: 2026-02-01T10:18:21Z
---

# RunManager: Prevent race condition in start_run

## 概要

`start_run` メソッドで、2つの同時呼び出しが両方ともアクティブなrunがないと判断し、複数のrunを作成してしまう競合状態の可能性。

## codex MCP レビューからの指摘

**場所**: `src/genglossary/runs/manager.py:69-77`

2つの同時呼び出し者が両方とも `get_active_run` で `None` を観測し、それぞれ別のrunを作成する可能性がある。

### 問題のシナリオ

```
Thread A                        Thread B
─────────────────────────────────────────────────
get_active_run() → None
                                get_active_run() → None
create_run() → run_id=1
                                create_run() → run_id=2
start thread for run_id=1
                                start thread for run_id=2
```

両方のrunが同時に実行され、データ競合や予期しない結果を招く可能性。

## 提案される解決策

### オプション1: プロセスローカルロックで `start_run` をシリアライズ

```python
class RunManager:
    def __init__(self, db_path: str):
        ...
        self._start_run_lock = Lock()

    def start_run(self, scope: str, triggered_by: str = "api") -> int:
        with self._start_run_lock:
            with database_connection(self.db_path) as conn:
                active_run = get_active_run(conn)
                if active_run is not None:
                    raise RuntimeError(f"Run already running: {active_run['id']}")

                with transaction(conn):
                    run_id = create_run(conn, scope=scope, triggered_by=triggered_by)

            # ... rest of the method
```

### オプション2: DB制約で一意性を強制

```sql
-- 1つのアクティブrunのみを許可する部分インデックス
CREATE UNIQUE INDEX IF NOT EXISTS idx_runs_active
ON runs ((1))
WHERE status IN ('pending', 'running');
```

### 推奨

オプション1が最もシンプルで、既存のコードへの影響が最小限。オプション2は複数プロセス間でも機能するが、スキーマ変更が必要。

## 影響範囲

- `src/genglossary/runs/manager.py`
- または `src/genglossary/db/schema.py`（オプション2の場合）

## Resolution

**重複チケット - 既に解決済み**

このチケットは `260130-runmanager-start-run-synchronization` で既に解決されています：
- `_start_run_lock` による排他制御が実装済み（manager.py:52, 71行目）
- 並行 `start_run()` のテストも追加済み（test_manager.py）
- 2026-01-31 にクローズ済み

## Tasks

- [x] 重複確認 - `260130-runmanager-start-run-synchronization` で解決済み
