---
priority: 2
tags: [ux, frontend, layout]
description: "Document Viewerで右側の用語タイルを常時表示（スティッキー）にする"
created_at: "2026-02-01T12:48:11Z"
started_at: 2026-02-01T23:03:53Z # Do not modify manually
closed_at: 2026-02-02T13:03:01Z # Do not modify manually
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

- [x] 右側パネルのスティッキーレイアウト実装
- [x] スクロール時の動作確認
- [x] 様々な画面サイズでのテスト
- [x] Commit
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Update docs/architecture/*.md
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing

## Implementation Summary

### Changes Made

1. **DocumentViewerPage.tsx**: GridからFlexboxレイアウトに変更
   - 高さの伝播問題を解決
   - 左右パネルの比率を7:5で維持

2. **DocumentPane.tsx**: Tabsに`h="100%"`を追加
   - ScrollAreaの高さ計算が正しく機能するように修正
   - スクロール問題を解決

3. **TermCard.tsx**: 全てのPaperに`position: sticky; top: 0`を追加
   - 用語タイルが常に画面上部に固定表示される

### Also Fixed

- tickets/260201-230132-document-viewer-scroll-fix.md のスクロール問題も同時に解決

## Notes

- CSS `position: sticky` を使用
- 用語タイルが長い場合は、タイル自体にスクロールを追加する必要があるかもしれない
