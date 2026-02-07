---
priority: 1
tags: [bugfix, frontend]
description: "Tabs disappear when required terms list is empty, forcing navigation to another page"
created_at: "2026-02-07T16:09:22Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# 必須用語が0件の場合にタブが消えて用語一覧に戻れなくなる

## 概要

必須用語一覧に1つも用語を登録していない状態で必須用語タブを表示すると、「用語一覧」「除外用語」「必須用語」のタブ自体が消えてしまう。再び用語一覧を表示するには別の機能画面に遷移してから戻る必要がある。

## 再現手順

1. Terms画面を開く（用語一覧/除外用語/必須用語のタブが表示されている）
2. 必須用語タブをクリック
3. 必須用語が0件の場合、タブが消える
4. 用語一覧に戻るには別画面に遷移してから戻るしかない

## 期待される動作

- 必須用語が0件でもタブは表示され続ける
- 空の状態では「必須用語はまだ登録されていません」等のメッセージを表示
- タブ間の遷移は常に可能

## Tasks

- [ ] 原因調査：タブが消える条件を特定（フロントエンドのレンダリングロジック）
- [ ] 修正実装：0件でもタブを維持するよう修正
- [ ] 空状態のUIメッセージを追加
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

- タブの表示条件がデータ件数に依存している可能性がある
- 除外用語タブでも同様の問題が発生するか確認が必要
