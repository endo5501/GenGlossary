---
priority: 8
tags: [gui, frontend, document-viewer]
description: "Document Viewer 完全実装"
created_at: "2026-01-27T16:33:25Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# Document Viewer 完全実装

## 概要

Document Viewer ページをスケルトン実装から完全実装にする。

## 現状の実装 (DocumentViewerPage.tsx)

```tsx
<Text c="dimmed">
  Document content will be displayed here for file ID: {fileId}
</Text>
```

スケルトン実装のみで、実際のドキュメント表示機能がない。

## 仕様 (plan-gui.md L118-128)

- 左ペイン: 原文（タブで文書選択、クリックで用語選択）
- 右ペイン: 用語カード（定義、出現箇所一覧、除外/編集/ジャンプボタン）

## 修正対象ファイル

- `frontend/src/pages/DocumentViewerPage.tsx`
- 必要に応じてバックエンドAPI追加

## Tasks

- [ ] 左ペイン: ドキュメント原文表示機能
- [ ] 左ペイン: タブでドキュメント選択
- [ ] 左ペイン: 用語クリックでハイライト
- [ ] 右ペイン: 用語カード（定義・出現箇所）
- [ ] 右ペイン: 除外/編集/ジャンプボタン
- [ ] バックエンドAPIの確認・追加（必要に応じて）
- [ ] playwright MCPを使用してDocument Viewerにプロジェクトのテキストが表示されることを確認
- [ ] playwright MCPを使用してDocument Viewerで用語クリックでハイライト・用語カードが表示されることを確認
- [ ] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [ ] Code simplification review using code-simplifier agent
- [ ] Code review by codex MCP
- [ ] Update docs/architecture/*.md
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## Notes

- 最も工数が大きいチケット
- ドキュメントの内容取得APIが必要
- 用語のハイライト機能は複雑な可能性
