---
priority: 2
tags: [improvement, backend, executor, type-safety]
description: "PipelineExecutor: Improve type safety and reduce type: ignore comments"
created_at: "2026-01-30T20:50:00Z"
started_at: null
closed_at: null
---

# PipelineExecutor: Improve type safety

## 概要

`_execute_full` メソッド内の `type: ignore` コメントを削減し、型安全性を向上させる。

## 現状の問題

**問題箇所**: `executor.py:313-326`

```python
for classified_term in extracted_terms:  # type: ignore[union-attr]
    classified_term: ClassifiedTerm  # type: ignore[no-redef]
    term_text = classified_term.term  # type: ignore[union-attr]
```

3箇所の `type: ignore` があり、型安全性が損なわれている。

## 原因

`extracted_terms` が `list[ClassifiedTerm]`（full scope）と `list[str]`（from_terms scope）の両方を受け入れるため、型チェッカーが正しく推論できない。

## 提案する解決策

### オプション1: メソッド分離

`_execute_full` 専用の用語処理ロジックを分離し、型を明確にする。

```python
def _process_classified_terms(
    self,
    conn: sqlite3.Connection,
    terms: list[ClassifiedTerm]
) -> list[ClassifiedTerm]:
    """ClassifiedTerm リストを処理し、重複を除去して保存"""
    ...
```

### オプション2: 入力の正規化

早期に統一された型に変換する。

```python
def _normalize_terms(
    self,
    terms: list[str] | list[ClassifiedTerm]
) -> list[ClassifiedTerm]:
    """入力を ClassifiedTerm リストに正規化"""
    ...
```

## 影響範囲

- `src/genglossary/runs/executor.py`

## Tasks

- [ ] 設計選択
- [ ] 実装
- [ ] テスト更新

## Notes

- code-simplifier レビューで指摘
- 型の混在はバグの温床になりやすい
