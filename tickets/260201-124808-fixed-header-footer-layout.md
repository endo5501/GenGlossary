---
priority: 2
tags: [ux, frontend, layout]
description: "Terms画面などで上部操作ボタンと下部ログを常時表示するレイアウトに修正"
created_at: "2026-02-01T12:48:08Z"
started_at: 2026-02-01T22:15:13Z # Do not modify manually
closed_at: 2026-02-01T22:45:47Z # Do not modify manually
---

# 上部・下部メニューの常時表示レイアウト

## 概要

Terms画面などで、上部に操作ボタン、下部にログ表示があるが、
内部のリストが長くなると見えなくなってしまう問題を修正する。

## 現状の問題

- リスト内の項目が多くなると、画面全体がスクロールされる
- 上部の操作ボタンや下部のログ表示がスクロールで見えなくなる
- 操作するたびにスクロールし直す必要があり、使い勝手が悪い

## 期待する動作

- 上部メニュー（操作ボタン）は常に画面上部に固定表示
- 下部メニュー（ログ表示）は常に画面下部に固定表示
- 中央のリスト部分のみがスクロールする

## 影響範囲

- Files画面
- Terms画面
- Provisional画面
- Issues画面
- Refined画面

## 設計

### 目標レイアウト（3層固定）

```
┌─────────────────────────────────┐
│ GlobalTopBar (既存の固定ヘッダー) │  ← 固定
├─────────────────────────────────┤
│ ActionBar (Extract, Add等)       │  ← 固定（新規）
├─────────────────────────────────┤
│                                 │
│ コンテンツ領域（リスト等）         │  ← スクロール
│                                 │
├─────────────────────────────────┤
│ LogPanel                        │  ← 固定
└─────────────────────────────────┘
```

### 実装アプローチ: AppShell + PageContainer レベルで修正

**1. AppShell.tsx**
- Main 内を Flexbox レイアウトに変更
- コンテンツ領域: `flex: 1`, `overflow: hidden`
- LogPanel: `flexShrink: 0` で高さ固定

**2. PageContainer.tsx**
- Flexbox レイアウトを追加
- ActionBar: `flexShrink: 0` で上部固定
- children: `flex: 1`, `overflow-y: auto` でスクロール

**3. FilesPage.tsx 等（PageContainer未使用ページ）**
- 同様の Flex パターンを適用

### 変更対象ファイル

1. `frontend/src/components/layout/AppShell.tsx`
2. `frontend/src/components/common/PageContainer.tsx`
3. `frontend/src/pages/FilesPage.tsx`
4. `frontend/src/pages/ProvisionalPage.tsx`
5. `frontend/src/pages/IssuesPage.tsx`
6. `frontend/src/pages/RefinedPage.tsx`

## Tasks

- [x] レイアウト構造の見直し（sticky/fixed positioning）
- [x] 中央コンテンツ部分のスクロール領域設定
- [x] 各画面での動作確認
- [x] Commit
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
  - Created ticket: 260201-223050-pagecontainer-code-simplification
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
  - Fixed: nested scroll issue, accessibility improvements
- [x] Update docs/architecture/*.md
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing


## Notes

- CSSの `position: sticky` または `position: fixed` を活用
- レスポンシブ対応も考慮する
