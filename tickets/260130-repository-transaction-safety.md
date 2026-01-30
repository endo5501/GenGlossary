---
priority: 1
tags: [improvement, backend, database, architecture]
description: "Repository layer: Transaction safety improvement"
created_at: "2026-01-30T20:40:00Z"
started_at: null
closed_at: null
---

# Repository layer: Transaction safety improvement

## 概要

リポジトリ層の各関数が内部で `conn.commit()` を呼び出しているため、トランザクション管理が呼び出し元でできない問題を解決する。

## 現状の問題

### リポジトリ関数が内部でコミット

例: `term_repository.py`
```python
def delete_all_terms(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    cursor.execute("DELETE FROM terms_extracted")
    conn.commit()  # 内部でコミット
```

### 影響

- PipelineExecutor でトランザクション管理ができない
- `_clear_tables_for_scope` の後にエラーが発生すると、データが削除された状態で残る
- ロールバックが効かない

## 提案する解決策

### オプション1: コミット責任の移譲

リポジトリ関数から `conn.commit()` を削除し、呼び出し元（executor, API等）でコミット管理する。

**メリット**: 最もシンプル、トランザクション制御が可能
**デメリット**: 既存のすべての呼び出し元を更新する必要がある

### オプション2: コンテキストマネージャ

トランザクションを明示的に管理するコンテキストマネージャを提供。

```python
@contextmanager
def transaction(conn):
    try:
        yield
        conn.commit()
    except:
        conn.rollback()
        raise
```

### オプション3: autocommit パラメータ

各リポジトリ関数に `autocommit=True` パラメータを追加し、デフォルトは現状維持。

## 影響範囲

- `src/genglossary/db/term_repository.py`
- `src/genglossary/db/document_repository.py`
- `src/genglossary/db/provisional_repository.py`
- `src/genglossary/db/refined_repository.py`
- `src/genglossary/db/issue_repository.py`
- `src/genglossary/db/runs_repository.py`
- `src/genglossary/runs/executor.py`
- API エンドポイント

## Tasks

- [ ] 設計レビュー・承認
- [ ] リポジトリ関数の修正
- [ ] 呼び出し元の更新
- [ ] テストの更新
- [ ] Commit
- [ ] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [ ] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket.
- [ ] Code review by codex MCP. If the issue is not addressed immediately, create a ticket.
- [ ] Update docs/architecture/*.md
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## Notes

- 260130-executor-improvements チケットから延期
- codex MCP レビューで Medium 優先度として指摘
