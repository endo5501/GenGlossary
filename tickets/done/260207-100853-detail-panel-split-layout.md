---
priority: 1
tags: [improvement, frontend, ux]
description: "Split list and detail panel into side-by-side layout to eliminate scrolling"
created_at: "2026-02-07T10:08:53Z"
started_at: 2026-02-07T12:04:00Z # Do not modify manually
closed_at: 2026-02-07T12:26:21Z # Do not modify manually
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

## 設計（確定）

### アプローチ: 新規 SplitLayout コンポーネント

`PageContainer` は変更せず、新規 `SplitLayout` コンポーネントを `children` として使う。

### SplitLayout コンポーネント仕様

```tsx
// frontend/src/components/common/SplitLayout.tsx

interface SplitLayoutProps {
  list: React.ReactNode           // 左側: リスト部分
  detail: React.ReactNode | null  // 右側: 詳細パネル (nullで非表示)
}
```

**動作:**
- `detail` が `null` → リストが全幅（100%）を使用
- `detail` が存在 → 左60%:右40%の分割レイアウト
- 左右それぞれ独立してスクロール可能（`overflow-y: auto`）
- レスポンシブ: 768px以下では縦並びにフォールバック

### CSS（layout.css に追加）

```css
.split-layout {
  display: flex;
  gap: var(--mantine-spacing-md);
  height: 100%;
  min-height: 0;
}

.split-layout-list {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

.split-layout-detail {
  flex: 0 0 40%;
  overflow-y: auto;
  min-height: 0;
}

@media (max-width: 768px) {
  .split-layout {
    flex-direction: column;
  }
  .split-layout-detail {
    flex: none;
  }
}
```

### 各ページへの適用パターン

```tsx
// Before:
<PageContainer actionBar={...}>
  <ListComponent />
  {selectedItem && <DetailPanel />}
</PageContainer>

// After:
<PageContainer actionBar={...}>
  <SplitLayout
    list={<ListComponent />}
    detail={selectedItem ? <DetailPanel /> : null}
  />
</PageContainer>
```

- **TermsPage**: list=Tabs全体, detail=選択用語の詳細パネル
- **ProvisionalPage**: list=テーブル, detail=編集パネル
- **RefinedPage**: list=Paperカード Stack, detail=詳細表示
- **IssuesPage**: list=フィルタ付きカード Stack, detail=issue詳細

各ページの内部ロジック（state, hooks, handlers）は変更なし。

### テスト方針

- SplitLayout のユニットテスト（detail null/非null の表示切替）
- 既存テストは data-testid が維持されるため通るはず

## Tasks

- [x] 共通 `SplitLayout` コンポーネント（またはPageContainer拡張）の設計・実装
- [x] レイアウトCSS（左右分割、独立スクロール）の追加
- [x] TermsPage: リストと詳細パネルを分割レイアウトに移行
- [x] ProvisionalPage: リストと詳細パネルを分割レイアウトに移行
- [x] RefinedPage: リストと詳細パネルを分割レイアウトに移行
- [x] IssuesPage: リストと詳細パネルを分割レイアウトに移行
- [x] レスポンシブ対応（狭い画面幅での縦並びフォールバック）
- [x] テスト: 各ページの選択・詳細表示の動作確認
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

- 幅比率: リスト60%:詳細40%（brainstorming で決定）
- 未選択時: 詳細パネル非表示、リスト全幅
- 既存のテスト（`data-testid` による詳細パネルの検証）が壊れないように注意
- `getRowSelectionProps` ユーティリティはそのまま利用可能
- `PageContainer` は変更しない
