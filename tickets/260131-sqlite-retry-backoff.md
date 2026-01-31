---
priority: 3
tags: [improvement, backend, reliability]
description: "Database: Add retry/backoff for transient SQLite locks"
created_at: "2026-01-31T15:20:00+09:00"
started_at: null
closed_at: null
---

# Database: Add retry/backoff for transient SQLite locks

## 概要

一時的なSQLiteロックエラー（"database is locked"）に対するリトライ/バックオフ機構がないため、ステータス更新が失敗してサイレントにドロップされる問題。

## codex MCP レビューからの指摘

**場所**: `src/genglossary/runs/manager.py:263-307`

`sqlite3.OperationalError: database is locked` が発生すると、ステータス更新は失敗としてマークされ、サイレントにドロップされる（現在はwarningログのみ）。

### 問題のシナリオ

1. バックグラウンドスレッドがDB更新を試行
2. 別のスレッド/プロセスがDBをロック中
3. `OperationalError: database is locked` が発生
4. ステータス更新が失敗し、runの状態が不整合に

## 提案される解決策

### オプション1: `_try_update_status` にリトライロジックを追加

```python
def _try_update_status(
    self,
    conn: sqlite3.Connection,
    run_id: int,
    error_message: str,
    max_retries: int = 3,
    backoff_base: float = 0.1,
) -> bool:
    """ステータス更新を試行（リトライ付き）"""
    for attempt in range(max_retries):
        try:
            with transaction(conn):
                update_run_status(...)
            return True
        except sqlite3.OperationalError as e:
            if "locked" in str(e) and attempt < max_retries - 1:
                time.sleep(backoff_base * (2 ** attempt))
                continue
            raise
        except Exception:
            return False
    return False
```

### オプション2: `get_connection` で `busy_timeout` を設定

```python
def get_connection(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.execute("PRAGMA busy_timeout = 5000")  # 5秒待機
    conn.row_factory = sqlite3.Row
    return conn
```

### 推奨

オプション2が最もシンプルで、すべてのDB操作に一貫して適用される。

## 影響範囲

- `src/genglossary/db/connection.py`
- または `src/genglossary/runs/manager.py`

## Tasks

- [ ] `busy_timeout` PRAGMA の追加を検討
- [ ] または `_try_update_status` にリトライロジックを追加
- [ ] テストの追加
- [ ] Commit
- [ ] Run static analysis (`pyright`) before reviewing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest`) before reviewing and pass all tests (No exceptions)
- [ ] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Update docs/architecture/*.md
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing
