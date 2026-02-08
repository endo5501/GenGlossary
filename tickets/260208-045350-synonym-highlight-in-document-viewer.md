---
priority: 1
tags: [feature, frontend]
description: "Synonym aliases are not highlighted in Document Viewer"
created_at: "2026-02-08T04:53:50Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# Document Viewerで同義語（aliases）がハイライトされない

## 概要

Document Viewer画面では、用語集の用語がドキュメント内でハイライト表示されるが、同義語グループのaliases（非代表用語）はハイライト対象に含まれていない。

例：代表用語「田中太郎」にaliases「田中」「田中部長」がある場合、ドキュメント内の「田中」「田中部長」はハイライトされない。

## 現状

- `DocumentViewerPage.tsx` で `term_name` のみを抽出してハイライト用の `terms` 配列を構築
- `DocumentPane.tsx` がその `terms` 配列を正規表現に変換してハイライト
- API応答の `GlossaryTermResponse.aliases` フィールドは既に利用可能だが未使用

## 期待される動作

- aliases もハイライト対象に含まれる
- aliases をクリックした場合、対応する代表用語の TermCard が選択される
- ハイライトの色は代表用語と同じ（代表用語と同一グループであることが視覚的にわかる）

## 調査ポイント

- `DocumentViewerPage.tsx`: terms 配列の構築ロジック（aliases を含める）
- `DocumentPane.tsx`: ハイライトクリック時の用語マッチングロジック（alias → 代表用語の逆引き）
- テスト: `document-viewer-page.test.tsx` にaliasesハイライトのテスト追加

## Tasks

- [ ] 原因調査：DocumentViewerPage の terms 構築ロジックを確認
- [ ] 修正実装（TDD）
- [ ] Commit
- [ ] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [ ] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Update docs (glob: "*.md" in ./docs/architecture)
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## Notes

- 前提チケット: `260207-161425-synonym-group-not-applied-in-results`（aliases フィールド追加済み）
- バックエンド修正は不要。フロントエンドのみの変更で対応可能
