---
priority: 4
tags: [frontend, ux]
description: "Terms画面でカテゴリを編集可能にする"
created_at: "2026-02-02T23:00:44Z"
started_at: null  # Do not modify manually
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
- [ ] 詳細パネル（term-detail-panel）にカテゴリ編集機能を追加
  - カテゴリ表示部分をクリックで編集モードに切り替え
  - または編集ボタンを追加してモーダル/インライン編集
- [ ] `useUpdateTerm` フックを `TermsPage` で利用
- [ ] 編集中の状態管理を実装
- [ ] 保存・キャンセル機能の実装
- [ ] ローディング状態の表示
- [ ] テーブル行でのインライン編集も検討（オプション）

### 品質タスク
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
