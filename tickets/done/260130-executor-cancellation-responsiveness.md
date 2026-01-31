---
priority: 3
tags: [improvement, backend, executor, ux]
description: "PipelineExecutor: Improve cancellation responsiveness during long operations"
created_at: "2026-01-30T20:50:00Z"
started_at: 2026-01-31T13:17:03Z
closed_at: 2026-01-31T13:41:08Z
---

# PipelineExecutor: Improve cancellation responsiveness

## 概要

ループ内や長時間の LLM 呼び出し中のキャンセルチェックを追加し、キャンセル応答性を向上させる。

## 現状の問題

**問題箇所**: `executor.py` 全体

キャンセルチェックは主要ステップ間でのみ行われ、以下の場合に遅延が発生：

1. **用語保存ループ内** (`executor.py:313-326`)
   - 大量の用語がある場合、ループ完了まで待つ必要がある

2. **LLM 呼び出し中**
   - `generator.generate()`, `reviewer.review()`, `refiner.refine()` は内部で複数の LLM 呼び出しを行う
   - 各呼び出しが完了するまでキャンセルが効かない

## 影響

- ユーザーがキャンセルボタンを押しても、長時間待たされる可能性
- キャンセル後も書き込みが継続する可能性（改善済み：refined 保存前チェック）

## 提案する解決策

### 1. ループ内キャンセルチェック

```python
for classified_term in extracted_terms:
    if self._check_cancellation():
        return
    # 処理
```

### 2. LLM クライアントへのキャンセルイベント伝播

GlossaryGenerator 等に cancel_event を渡し、各 LLM 呼び出し間でチェック。

```python
generator.generate(
    terms, documents,
    cancel_event=self._cancel_event,
    term_progress_callback=progress_cb
)
```

## 影響範囲

- `src/genglossary/runs/executor.py`
- `src/genglossary/glossary_generator.py`
- `src/genglossary/glossary_refiner.py`
- `src/genglossary/glossary_reviewer.py`

## Tasks

- [x] ループ内キャンセルチェック追加
- [x] LLM 処理クラスへの cancel_event 対応
- [x] テスト更新
- [x] Commit
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Update docs/architecture/*.md
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing

## Notes

- codex MCP レビューで Low 優先度として指摘
- UX 改善として有用

## 実施内容サマリー

### 1. LLM 処理クラスへの cancel_event 対応
- `GlossaryGenerator.generate()`: ループ前と各用語処理前にキャンセルチェック
- `GlossaryReviewer.review()`: LLM呼び出し前にキャンセルチェック、戻り値を `list[GlossaryIssue] | None` に変更
- `GlossaryRefiner.refine()`: ループ前と各issue処理前にキャンセルチェック

### 2. Executor での対応
- 各 LLM 処理クラスに `cancel_event=context.cancel_event` を渡すよう変更
- provisional glossary 保存前にキャンセルチェック追加
- `issues is None` の処理（レビューキャンセル時）を追加

### 3. CLI/CLI_DB での対応
- `review()` の戻り値が `None` になる可能性に対応（型安全性）

### 4. ドキュメント更新
- `docs/architecture/runs.md`: LLM 処理クラスへのキャンセルイベント伝播のセクション追加
