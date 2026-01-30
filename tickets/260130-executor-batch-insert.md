---
priority: 3
tags: [improvement, backend, executor, performance]
description: "PipelineExecutor: Batch database inserts for better performance"
created_at: "2026-01-30T20:50:00Z"
started_at: null
closed_at: null
---

# PipelineExecutor: Batch database inserts

## 概要

個別 INSERT を executemany によるバッチ処理に変更し、大量データ処理時のパフォーマンスを向上させる。

## 現状の問題

**問題箇所**: `executor.py` 複数箇所

```python
# documents
for document in documents:
    create_document(conn, ...)

# terms
for classified_term in extracted_terms:
    create_term(conn, ...)

# issues
for issue in issues:
    create_issue(conn, ...)
```

各行で個別に INSERT が実行され、暗黙のトランザクションが多数作成される。

## 影響

- 大量の用語・ドキュメントを処理する場合にパフォーマンス低下
- トランザクション安全性チケット（260130-repository-transaction-safety）と関連

## 提案する解決策

### リポジトリ層にバッチ関数を追加

```python
def create_terms_batch(
    conn: sqlite3.Connection,
    terms: list[tuple[str, str | None]]  # (term_text, category)
) -> None:
    cursor = conn.cursor()
    cursor.executemany(
        "INSERT INTO terms_extracted (term_text, category) VALUES (?, ?)",
        terms
    )
```

## 影響範囲

- `src/genglossary/db/term_repository.py`
- `src/genglossary/db/document_repository.py`
- `src/genglossary/db/issue_repository.py`
- `src/genglossary/runs/executor.py`

## Tasks

- [ ] 設計
- [ ] リポジトリにバッチ関数追加
- [ ] executor でバッチ関数を使用
- [ ] パフォーマンステスト
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

- codex MCP レビューで Low 優先度として指摘
- 260130-repository-transaction-safety と組み合わせて対応推奨
