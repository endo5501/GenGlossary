---
priority: 7
tags: [backend, edge-case]
description: "Review step: emit initial step update for empty glossary"
created_at: "2026-02-02T14:26:32Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# Review step: emit initial step update for empty glossary

## 概要

レビューステップで、用語集が空の場合や最初のバッチコールバックが呼ばれる前に例外が発生した場合、`current_step` が更新されないため、UIが前のステップを「処理中」として表示し続ける可能性がある。

## 現状の問題

- `_do_review` メソッドは `on_batch_progress` コールバックが呼ばれたときにのみ `step='issues'` を設定
- 用語集が空（term_count == 0）の場合、コールバックが一度も呼ばれない可能性
- 例外が発生した場合も、ステップが更新されないまま終了

## 期待する動作

- レビューステップ開始時に、初期の進捗更新（`step='issues'`）を送信
- これによりUIが即座に「Issues」メニューにスピナーを表示

## Tasks

- [ ] `_do_review` の開始時に初期進捗更新を追加
- [ ] 空の用語集でのテストケース追加
- [ ] Commit
- [ ] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [ ] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Update docs/architecture/*.md
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing


## Notes

- Codex MCP レビューで指摘された問題
- 軽微なエッジケースのため priority: 7
