---
priority: 3
tags: [ux, frontend]
description: "Terms抽出画面に進捗ログ・作業開始メッセージを表示する"
created_at: "2026-02-01T12:48:07Z"
started_at: 2026-02-02T13:18:22Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# Terms抽出の進捗ログ表示

## 概要

Terms（用語）の抽出処理はかなり時間がかかるため、ユーザーに進捗を伝えるログ表示が必要。
最低限、作業を開始したことを示すメッセージを表示すべき。

## 現状の問題

- Terms抽出処理が開始されても、ユーザーに何もフィードバックがない
- 処理が進んでいるのか、止まっているのか判断できない

## 期待する動作

- 処理開始時に「用語抽出を開始しました」等のメッセージを表示
- 可能であれば、処理の進捗状況（処理中のドキュメント名など）を表示

## Tasks

- [x] 処理開始時のメッセージ表示を実装
- [x] 進捗ログの表示機能を実装（任意）
- [x] Commit
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Update docs/architecture/*.md
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing


## Notes

- 他のLLM処理（GlossaryGenerator, GlossaryReviewer, GlossaryRefiner）も同様に進捗表示が必要な場合は、共通コンポーネントとして実装を検討
