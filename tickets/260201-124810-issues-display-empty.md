---
priority: 1
tags: [bug, frontend, critical]
description: "Issues画面に何も表示されなくなった"
created_at: "2026-02-01T12:48:10Z"
started_at: 2026-02-01T13:12:22Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# Issues画面が空になる問題

## 概要

Issues画面に何も表示されなくなった。

## 現状の問題

- Issues画面を開いても、コンテンツが表示されない
- 以前は正常に表示されていた

## 期待する動作

- GlossaryReviewerで検出されたIssue（問題点）の一覧が表示される
- 各Issueの詳細情報が確認できる

## 再現手順

1. パイプラインを実行してIssuesステップまで完了させる
2. サイドバーからIssuesを選択
3. → 画面が空（期待: Issueの一覧が表示される）

## 調査ポイント

- データ取得APIが正しく動作しているか
- フロントエンドのレンダリングロジックに問題がないか
- データの形式が変わっていないか

## Tasks

- [x] バックエンドAPIの動作確認
- [x] フロントエンドのコンソールエラー確認
- [x] データフローの調査
- [x] 修正実装
- [x] Commit
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Update docs/architecture/*.md (変更不要 - バックエンドと同期済み)
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing


## Notes

- リグレッションバグの可能性
- 最近の変更履歴を確認する
