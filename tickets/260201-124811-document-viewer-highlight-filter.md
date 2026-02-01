---
priority: 2
tags: [bug, frontend]
description: "Document ViewerでCOMMON_NOUNの単語がハイライトされる問題を修正"
created_at: "2026-02-01T12:48:11Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# Document Viewer ハイライトフィルタリング

## 概要

Document Viewerにて、「COMMON_NOUN」と判断されて解析が行われていない単語も
ハイライトされている問題を修正する。

## 現状の問題

- 全ての抽出された単語がハイライトされている
- COMMON_NOUN（一般名詞）として除外された単語もハイライトされている
- どの単語が実際に用語集に含まれているかわかりにくい

## 期待する動作

- Provisional（暫定用語集）で解析が行われた単語のみをハイライトする
- COMMON_NOUNやその他の理由で除外された単語はハイライトしない
- ハイライトされた単語は、用語集に含まれる用語と一致する

## Tasks

- [ ] ハイライト対象の単語フィルタリングロジック修正
- [ ] Provisionalの用語リストと照合してハイライト
- [ ] 動作確認
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

- COMMON_NOUN以外にも除外理由があれば、それらも考慮する
- パフォーマンスへの影響を確認する
