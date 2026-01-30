---
priority: 3
tags: [improvement, backend, database]
description: "Add nested transaction safety using SAVEPOINT"
created_at: "2026-01-30T22:20:00Z"
started_at: null
closed_at: null
---

# Add nested transaction safety using SAVEPOINT

## 概要

現在の `transaction()` コンテキストマネージャは、ネストした使用に対して安全ではない。内側のトランザクションが `commit()` を呼び出すと、外側のトランザクションの作業単位が早期にコミットされてしまう。

## 現状の問題

```python
with transaction(conn):  # 外側
    create_term(conn, "term1", ...)
    with transaction(conn):  # 内側 - これが commit() を呼ぶと外側も終了
        create_term(conn, "term2", ...)
    # ここで例外が発生しても、term2 は既にコミット済み
```

## 提案する解決策

`SAVEPOINT` を使用してネストをサポートする:

```python
@contextmanager
def transaction(conn: sqlite3.Connection) -> Iterator[None]:
    if conn.in_transaction:
        # ネストされたトランザクション - SAVEPOINT を使用
        savepoint_name = f"sp_{uuid.uuid4().hex[:8]}"
        conn.execute(f"SAVEPOINT {savepoint_name}")
        try:
            yield
            conn.execute(f"RELEASE {savepoint_name}")
        except Exception:
            conn.execute(f"ROLLBACK TO {savepoint_name}")
            raise
    else:
        # トップレベルのトランザクション
        try:
            yield
            conn.commit()
        except Exception:
            conn.rollback()
            raise
```

## 影響範囲

- src/genglossary/db/connection.py

## Tasks

- [ ] 設計レビュー・承認
- [ ] SAVEPOINT を使用したネストサポートの実装
- [ ] テストの追加
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

- 260130-repository-transaction-safety チケットの codex MCP レビューで指摘
- 現時点では実際にネストされた呼び出しは行われていないが、将来的なリスク防止のため
