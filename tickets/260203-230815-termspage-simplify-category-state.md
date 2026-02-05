---
priority: 3
tags: [frontend, refactoring]
description: "TermsPage: simplify category editing state management"
created_at: "2026-02-03T23:08:15Z"
started_at: 2026-02-05T22:18:54Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# TermsPage: カテゴリ編集の状態管理をシンプル化

## 概要

code-simplifier agentによるレビュー結果に基づき、TermsPageのカテゴリ編集機能の状態管理をシンプル化する。

## 現状

現在、カテゴリ編集に2つの独立した状態を使用している：
- `isEditingCategory: boolean`
- `editingCategoryValue: string`

## 改善案

単一の状態に統合することで、コードをシンプル化できる：

```typescript
// オプション: editingCategoryValueがnullかどうかで編集モードを判定
const [editingCategoryValue, setEditingCategoryValue] = useState<string | null>(null)
const isEditingCategory = editingCategoryValue !== null
```

## Tasks

- [x] 2つの状態を1つに統合
- [x] リセットロジックの共通化（既に`resetCategoryEdit`として抽出済み）
- [x] Commit
- [x] Run tests (`pnpm test`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing

## Notes

- 優先度は低いため、他の重要なタスクを優先すること
- 関連ファイル: `frontend/src/pages/TermsPage.tsx`
