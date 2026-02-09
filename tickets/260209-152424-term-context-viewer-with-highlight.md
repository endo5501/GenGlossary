---
priority: 2
tags: [feature, frontend, terms, ux]
description: "ドキュメント上で用語をハイライト表示し、文脈を見ながら除外・必須登録できる新UIを追加"
created_at: "2026-02-09T15:24:24Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# ドキュメント上での用語ハイライト＆除外/必須登録UI

## 問題

現在のTerms画面（`TermsPage`）では、抽出された用語がテーブル形式（単語の羅列）で表示される。ユーザーはここから除外用語・必須用語を登録できるが、以下の問題がある：

- 用語が**どのような文脈で使われているか**がわからない
- 元のドキュメントを確認しないと、除外すべきか必須にすべきか判断しにくい
- ドキュメントを読んでいて「この単語も用語として登録したい」と思っても、Terms画面に戻って手動入力する必要がある

## 提案する新UI

DocumentViewerのように**元のドキュメントを表示**し、その上で用語操作を行える新しいインタフェースを追加する。

### 主な機能

1. **ドキュメント表示 + 用語ハイライト**
   - 登録済みドキュメントをファイルタブで切り替え表示
   - 抽出済み用語をドキュメント内でハイライト表示
   - 除外済み用語・必須用語は色分けして識別可能にする

2. **ハイライト用語の操作（クリック/コンテキストメニュー）**
   - ハイライトされた用語をクリック → 除外用語に追加
   - 用語の詳細情報（カテゴリ等）をポップオーバーで表示

3. **テキスト選択による必須用語登録**
   - ドキュメント内の任意のテキストを選択 → 必須用語として登録
   - ピックアップされていない単語を必須用語に追加できる

4. **フィルタ/凡例**
   - ハイライトの色凡例（通常用語 / 除外済み / 必須用語）
   - ハイライト表示のON/OFFトグル

## 既存資産の活用

既存のDocumentViewerコンポーネントには、活用可能な以下の機能がある：

### DocumentPane（`components/document-viewer/DocumentPane.tsx`）
- ファイルタブ切り替え表示
- 正規表現による用語ハイライト（長い用語優先マッチ）
- O(1)ルックアップによるパフォーマンス最適化
- クリックで用語選択

### TermCard（`components/document-viewer/TermCard.tsx`）
- 用語の定義・出現箇所の表示

### 既存APIフック
- `useTerms()` - 抽出済み用語取得
- `useExcludedTerms()` / `useCreateExcludedTerm()` / `useDeleteExcludedTerm()`
- `useRequiredTerms()` / `useCreateRequiredTerm()` / `useDeleteRequiredTerm()`
- `useFileDetail()` - ドキュメントコンテンツ取得
- `useFiles()` - ファイル一覧取得

## 関連ファイル

### 既存UI（参考・流用元）
- `frontend/src/pages/TermsPage.tsx` - 現在のTerms画面（3タブ構成）
- `frontend/src/pages/DocumentViewerPage.tsx` - ドキュメントビューア
- `frontend/src/components/document-viewer/DocumentPane.tsx` - ドキュメント表示+ハイライト
- `frontend/src/components/document-viewer/TermCard.tsx` - 用語詳細カード
- `frontend/src/components/common/TermListTable.tsx` - 用語テーブル
- `frontend/src/components/common/AddTermModal.tsx` - 用語追加モーダル

### APIフック
- `frontend/src/api/hooks/useTerms.ts`
- `frontend/src/api/hooks/useExcludedTerms.ts`
- `frontend/src/api/hooks/useRequiredTerms.ts`
- `frontend/src/api/hooks/useFiles.ts`

### 技術スタック
- React 19 + TypeScript
- Mantine UI 8
- TanStack Query（データフェッチ）
- TanStack Router（ルーティング）

## Tasks

- [ ] 調査：既存DocumentPaneのハイライト機能を新UIに流用できる範囲を確認
- [ ] 設計：新ページ/コンポーネントの構成とルーティング設計
- [ ] 設計：ハイライトの色分けルール（通常用語/除外済み/必須用語）
- [ ] 設計：用語操作のUXフロー（クリック→除外、テキスト選択→必須登録）
- [ ] 実装：新ページコンポーネント作成（ルーティング追加）
- [ ] 実装：ドキュメント表示 + 用語種別ごとの色分けハイライト
- [ ] 実装：ハイライト用語クリックで除外操作（ポップオーバー）
- [ ] 実装：テキスト選択による必須用語登録
- [ ] 実装：凡例・フィルタUI
- [ ] テスト：ハイライト表示の正確性
- [ ] テスト：除外/必須登録操作の動作確認
- [ ] テスト：既存Terms画面・DocumentViewerへの影響がないこと
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

- 既存のDocumentViewerPageは用語集（Glossary）表示が目的。新UIは用語抽出段階での操作が目的なので、別ページとして作成する方が適切
- DocumentPaneのハイライトロジックは共通化して再利用できる可能性が高い
- 既存のTermsPage（テーブル表示）は残す。新UIはTermsページ内の新しいタブ、または独立したページとして追加する（設計時に決定）
- バックエンドAPI変更は不要の見込み（既存APIで対応可能）
