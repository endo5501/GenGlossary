---
priority: 1
tags: [improvement, frontend, ux]
description: "Split list and detail panel into side-by-side layout to eliminate scrolling"
created_at: "2026-02-07T10:08:53Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# 詳細パネルのレイアウト改善（リスト・詳細の分割表示）

## 概要

現在、Terms、Provisional、Refined、Issues の各画面では、アイテムを選択するとその詳細がリストの**下部**に表示される。リストと詳細パネルが同じスクロールコンテナ（`.scrollable-content`）内に縦並びで配置されているため、例えばリスト最上部の用語を選択しても、詳細を確認するにはページ最下部までスクロールする必要があり、操作性が悪い。

## 現在のレイアウト

```
┌──────────────────────────────┐
│ Action Bar                   │
├──────────────────────────────┤
│ .scrollable-content          │
│ ┌──────────────────────────┐ │
│ │ リスト (Table/Cards)     │ │
│ │ ...                      │ │
│ │ ...（長いリスト）         │ │
│ │ ...                      │ │
│ └──────────────────────────┘ │
│ ┌──────────────────────────┐ │
│ │ 詳細パネル ← スクロール  │ │
│ │              しないと     │ │
│ │              見えない     │ │
│ └──────────────────────────┘ │
└──────────────────────────────┘
```

## 改善後のレイアウト

リストと詳細パネルを**左右分割**にし、詳細パネルがスクロールなしで常に表示されるようにする。

```
┌──────────────────────────────────────┐
│ Action Bar                           │
├──────────────────┬───────────────────┤
│ リスト           │ 詳細パネル        │
│ (スクロール可)   │ (固定表示)        │
│                  │                   │
│ ▶ 選択中の用語   │ 用語名: xxx       │
│   用語2          │ カテゴリ: xxx     │
│   用語3          │ 出現箇所: ...     │
│   ...            │                   │
│                  │                   │
└──────────────────┴───────────────────┘
```

## 対象ページ（4画面共通の問題）

| ページ | ファイル | 詳細パネル |
|--------|----------|-----------|
| Terms | `TermsPage.tsx` | `term-detail-panel` (行274-346) |
| Provisional | `ProvisionalPage.tsx` | `provisional-detail-editor` (行119-166) |
| Refined | `RefinedPage.tsx` | `refined-detail-panel` (行86-102) |
| Issues | `IssuesPage.tsx` | 詳細パネル (行103-121) |

## 実装方針

### レイアウト構造の変更

現在の `.scrollable-content` 内の縦並びレイアウトを、左右分割レイアウトに変更する。

**方針案: CSS Flexbox / Grid による左右分割**

```
.scrollable-content
  ├── .list-panel     (左: スクロール可、flex: 1)
  └── .detail-panel   (右: 固定幅 or flex比率、独立スクロール)
```

- リスト部分は独立してスクロール可能
- 詳細パネルは選択時に右側に表示（未選択時はリストが全幅）
- 詳細パネルも内容が長い場合は独立してスクロール可能

### 共通コンポーネント化の検討

4ページすべてで同じパターンのため、共通の `SplitLayout` コンポーネント（またはPageContainerの拡張）を作成することを検討する。

```tsx
// 案: SplitLayoutコンポーネント
<SplitLayout
  list={<Table>...</Table>}
  detail={selectedItem && <DetailPanel>...</DetailPanel>}
/>
```

### レスポンシブ対応

- 画面幅が狭い場合は現在の縦並びレイアウトにフォールバック
- ブレークポイントの目安: 768px 以下で縦並び

## Tasks

- [ ] 共通 `SplitLayout` コンポーネント（またはPageContainer拡張）の設計・実装
- [ ] レイアウトCSS（左右分割、独立スクロール）の追加
- [ ] TermsPage: リストと詳細パネルを分割レイアウトに移行
- [ ] ProvisionalPage: リストと詳細パネルを分割レイアウトに移行
- [ ] RefinedPage: リストと詳細パネルを分割レイアウトに移行
- [ ] IssuesPage: リストと詳細パネルを分割レイアウトに移行
- [ ] レスポンシブ対応（狭い画面幅での縦並びフォールバック）
- [ ] テスト: 各ページの選択・詳細表示の動作確認
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

- Mantine UIの `Grid` や `SimpleGrid` コンポーネントの利用も検討可能
- 詳細パネルの幅比率は brainstorming 時に決定（リスト60%:詳細40% 程度が目安）
- 既存のテスト（`data-testid` による詳細パネルの検証）が壊れないように注意
- `getRowSelectionProps` ユーティリティはそのまま利用可能
