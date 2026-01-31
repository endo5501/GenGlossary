---
priority: 3
tags: [improvement, backend, executor, ux]
description: "PipelineExecutor: Improve cancellation responsiveness during long operations"
created_at: "2026-01-30T20:50:00Z"
started_at: null
closed_at: null
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

- [ ] ループ内キャンセルチェック追加
- [ ] LLM 処理クラスへの cancel_event 対応
- [ ] テスト更新
- [ ] Commit
- [ ] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest`) before reviwing and pass all tests (No exceptions)
- [ ] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Update docs/architecture/*.md
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## Notes

- codex MCP レビューで Low 優先度として指摘
- UX 改善として有用
