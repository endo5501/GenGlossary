---
priority: 4
tags: [frontend, ux]
description: "Terms画面でカテゴリを編集可能にする"
created_at: "2026-02-02T23:00:44Z"
started_at: 2026-02-03T22:59:20Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# Terms画面でカテゴリ編集機能を追加

## 概要

現在、Terms画面に表示されるカテゴリはFilesからの抽出時にLLMが自動で付与しています。しかし、このカテゴライズが誤っていることがあるため、ユーザーがTerms画面上でカテゴリを手動で変更できる機能を追加します。

## 現状分析

### 既存のコード状況
- **フロントエンド**: `useUpdateTerm` フックが既に存在（`frontend/src/api/hooks/useTerms.ts:63-74`）
- **バックエンド**: `PATCH /api/projects/{project_id}/terms/{term_id}` APIが既に存在
- **スキーマ**: `TermUpdateRequest` で `term_text` と `category` の更新が可能

### 実装すべき箇所
- `TermsPage.tsx` にカテゴリ編集UIを追加

## Tasks

### 実装タスク
- [x] 詳細パネル（term-detail-panel）にカテゴリ編集機能を追加
  - カテゴリ表示部分をクリックで編集モードに切り替え
  - または編集ボタンを追加してモーダル/インライン編集
- [x] `useUpdateTerm` フックを `TermsPage` で利用
- [x] 編集中の状態管理を実装
- [x] 保存・キャンセル機能の実装
- [x] ローディング状態の表示
- [x] テーブル行でのインライン編集も検討（オプション） → 詳細パネルのみで実装

### 品質タスク
- [x] Commit
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
  - → チケット作成: `tickets/260203-230815-termspage-simplify-category-state.md`
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
  - → 指摘されたバグを修正済み（選択変更時の編集状態リセット、ダブルサブミット防止、アクセシビリティ改善）
- [x] Update docs/architecture/*.md
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing


## Design

### 概要

詳細パネル（`term-detail-panel`）内のカテゴリ表示部分にインライン編集機能を追加。Badge の横に編集アイコンを配置し、クリックでテキスト入力に切り替わる。

### UI動作フロー

```
[通常表示]
  Category: [Badge: 技術用語] [✏️]

     ↓ 編集アイコンクリック

[編集モード]
  Category: [TextInput: 技術用語____] [✓] [✗]

     ↓ ✓クリック or Enter

[保存中]
  Category: [TextInput: disabled] [spinner]

     ↓ 成功

[通常表示に戻る]
```

### 変更ファイル

- `frontend/src/pages/TermsPage.tsx` のみ

### 実装内容

1. **状態追加**: `isEditingCategory`, `editingCategoryValue`
2. **useUpdateTerm フック追加**: 既存フックをimport
3. **詳細パネル内UIの変更**:
   - 通常時: Badge + 編集アイコン（IconPencil）
   - 編集時: TextInput + 保存/キャンセルボタン
4. **保存処理**: 空文字は `null` として送信（カテゴリ削除）

## Notes

### UI/UX 検討事項
1. **編集方法の選択肢**:
   - インライン編集（Badge をクリックして直接編集）
   - モーダル編集（編集ボタンでモーダルを開く）
   - 詳細パネル内での編集

2. **カテゴリ入力方式**:
   - 自由テキスト入力
   - 既存カテゴリからの選択（ドロップダウン/オートコンプリート）
   - 両方を組み合わせ

3. **バリデーション**:
   - 空文字の場合は `null` として保存（カテゴリなし）
   - 最大文字数の制限（検討）

### 関連ファイル
- `frontend/src/pages/TermsPage.tsx` - メイン実装箇所
- `frontend/src/api/hooks/useTerms.ts` - `useUpdateTerm` フック
- `frontend/src/api/types.ts` - `TermUpdateRequest` 型定義
