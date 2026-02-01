---
priority: 2
tags: [bug, frontend]
description: "Document Viewerで上下スクロールが効かない問題を修正"
created_at: "2026-02-01T23:01:32Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# Document Viewer スクロール問題の修正

## 概要

Document Viewerにおいて、ドキュメント表示エリアの上下スクロールが効かなくなっている問題を修正する。

## 現状の問題

- Document Viewerでドキュメントを表示した際、コンテンツが長くてもスクロールできない
- マウスホイールやスクロールバーが機能していない可能性

## 調査ポイント

- `DocumentPane.tsx`のScrollAreaコンポーネントの設定
- 親コンテナの高さ設定（`h="100%"`など）
- CSSのoverflow設定

## Tasks

- [ ] 問題の再現と原因調査
- [ ] スクロール機能の修正
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

- DocumentPane.tsxの91行目にScrollAreaがある
- 高さの計算 `h="calc(100% - 42px)"` が正しく機能しているか確認が必要
