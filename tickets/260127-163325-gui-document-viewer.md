---
priority: 2
tags: [gui, frontend, document-viewer]
description: "Document Viewer 完全実装"
created_at: "2026-01-27T16:33:25Z"
started_at: 2026-02-01T11:42:32Z # Do not modify manually
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

## 設計

### アーキテクチャ概要

```
┌─────────────────────────────────────────────────────────────┐
│                    DocumentViewerPage                        │
├─────────────────────────────┬───────────────────────────────┤
│      左ペイン (60%)          │       右ペイン (40%)           │
│  ┌─────────────────────┐    │   ┌───────────────────────┐   │
│  │  ドキュメントタブ      │    │   │     用語カード         │   │
│  │  [doc1] [doc2] ...  │    │   │                       │   │
│  ├─────────────────────┤    │   │  用語名: ○○○          │   │
│  │                     │    │   │  定義: ...            │   │
│  │  ドキュメント本文      │    │   │  出現箇所: ...        │   │
│  │  (用語ハイライト付き)  │    │   │                       │   │
│  │                     │    │   │  [除外][編集][ジャンプ] │   │
│  └─────────────────────┘    │   └───────────────────────┘   │
└─────────────────────────────┴───────────────────────────────┘
```

**コンポーネント構成:**
- `DocumentViewerPage.tsx` - メインコンテナ（状態管理）
- `DocumentPane.tsx` - 左ペイン（タブ + 本文表示）
- `TermCard.tsx` - 右ペイン（用語詳細表示）

### バックエンドAPI変更

**変更対象:** `GET /api/projects/{project_id}/files/{file_id}`

現在のレスポンスに `content` フィールドを追加:
```json
{
  "id": 1,
  "file_name": "chapter1.md",
  "content_hash": "abc123...",
  "content": "ドキュメントの本文..."
}
```

**変更ファイル:**
- `src/genglossary/api/schemas/file_schemas.py` - `FileDetailResponse`スキーマ追加
- `src/genglossary/api/routers/files.py` - 詳細取得時にcontent含める
- `frontend/src/api/types.ts` - `FileDetailResponse`型追加
- `frontend/src/api/hooks/useFiles.ts` - `useFileDetail`フック追加

### フロントエンド実装

**状態管理（DocumentViewerPage）:**
- `selectedFileId: number | null` - 選択中のドキュメント
- `selectedTerm: string | null` - 選択中の用語テキスト

**左ペイン（DocumentPane）:**
- ファイル一覧をタブ表示、選択ファイルのcontentを表示
- 用語リストから本文中の該当テキストをクリッカブルに
- クリックで`onTermSelect(termText)`を呼び出し

**右ペイン（TermCard）:**
- Refined優先、なければProvisionalにフォールバック
- 定義と出現箇所を表示
- ボタンはdisabled状態で配置（初期実装）

### データフロー

**ページ読み込み時:**
1. `useFiles(projectId)` → ファイル一覧取得
2. `useTerms(projectId)` → 用語一覧取得（ハイライト用）
3. `useRefined(projectId)` → Refined用語集取得
4. `useProvisional(projectId)` → Provisional用語集取得

**ファイル選択時:**
5. `useFileDetail(projectId, fileId)` → 選択ファイルのcontent取得

**用語クリック時:**
- ローカル状態更新のみ（追加API呼び出しなし）

## Tasks

- [x] `/brainstorming` skillを使用して計画を明確にする
- [x] Phase 1: バックエンドAPI
  - [x] `FileDetailResponse`スキーマ追加（contentフィールド付き）
  - [x] `GET /files/{file_id}` でcontentを返すよう修正
  - [x] APIテスト追加
- [x] Phase 2: フロントエンド型・フック
  - [x] `FileDetailResponse`型追加
  - [x] `useFileDetail`フック追加
- [x] Phase 3: UIコンポーネント
  - [x] `DocumentPane`コンポーネント作成（タブ + 本文表示）
  - [x] `TermCard`コンポーネント作成（用語詳細表示）
  - [x] `DocumentViewerPage`を左右2ペイン構成に変更
- [x] Phase 4: 用語ハイライト
  - [x] 本文中の用語をクリッカブルにする機能実装
  - [x] 選択用語のハイライト表示
- [x] Phase 5: 統合テスト
  - [x] playwright MCPを使用してDocument Viewerにプロジェクトのテキストが表示されることを確認
  - [x] playwright MCPを使用してDocument Viewerで用語クリックでハイライト・用語カードが表示されることを確認
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
  - Created ticket: 260201-120133-code-simplification-file-schemas-viewer.md
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
  - Created ticket: 260201-120325-document-viewer-performance-optimization.md
- [x] Update docs/architecture/*.md
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing

## Notes

- 最も工数が大きいチケット
- ドキュメントの内容取得APIが必要
- 用語のハイライト機能は複雑な可能性
