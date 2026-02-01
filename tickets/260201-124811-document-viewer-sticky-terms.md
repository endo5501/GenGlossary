---
priority: 2
tags: [ux, frontend, layout]
description: "Document Viewerで右側の用語タイルを常時表示（スティッキー）にする"
created_at: "2026-02-01T12:48:11Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# Document Viewer 用語タイルの常時表示

## 概要

Document Viewerにて、画面をスクロールすると右側の用語タイルが見えなくなってしまう。
左のドキュメントをスクロールしても、用語タイルは常に表示されているべき。

## 現状の問題

- ドキュメントをスクロールすると、右側の用語タイル（パネル）も一緒にスクロールされて見えなくなる
- 用語の定義を確認しながらドキュメントを読むことが困難

## 期待する動作

- 左側：ドキュメント表示エリア（スクロール可能）
- 右側：用語タイル（スティッキー表示、常に画面に固定）
- ドキュメントをスクロールしても、用語タイルは常に画面右側に表示される

## Tasks

- [ ] 右側パネルのスティッキーレイアウト実装
- [ ] スクロール時の動作確認
- [ ] 様々な画面サイズでのテスト
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

- CSS `position: sticky` を使用
- 用語タイルが長い場合は、タイル自体にスクロールを追加する必要があるかもしれない
