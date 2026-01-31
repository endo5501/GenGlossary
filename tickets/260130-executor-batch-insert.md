---
priority: 3
tags: [improvement, backend, executor, performance]
description: "PipelineExecutor: Batch database inserts for better performance"
created_at: "2026-01-30T20:50:00Z"
started_at: 2026-01-31T04:57:25Z
closed_at: 2026-01-31T12:45:52Z
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

- [x] 設計
- [x] リポジトリにバッチ関数追加
- [x] executor でバッチ関数を使用
- [x] パフォーマンステスト (省略)
- [x] Commit
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
  - チケット作成: 260131-050758-refactor-batch-insert-common-helper.md
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
  - 修正済み: create_glossary_terms_batch のバリデーション順序
- [x] Update docs/architecture/*.md
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing

## Notes

- codex MCP レビューで Low 優先度として指摘
- 260130-repository-transaction-safety と組み合わせて対応推奨
