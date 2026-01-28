# チケット作成計画: Files画面 Add ボタン機能実装

## 問題の概要

Files画面の「Add」ボタンをクリックしても何も起きない。

## 調査結果

### 現状
- **Add ボタンの場所**: `frontend/src/pages/FilesPage.tsx` (Line 140)
- **問題**: `onClick` ハンドラが設定されていない

```typescript
// 現在のコード（onClickなし）
<Button leftSection={<IconPlus size={16} />}>Add</Button>
```

### 既に実装済みの部分
| 項目 | 状態 | ファイル |
|------|------|---------|
| API エンドポイント | 実装済み | `POST /api/projects/{projectId}/files` |
| Mutation フック | 実装済み | `useCreateFile(projectId)` in `api/hooks/useFiles.ts` |
| Mock ハンドラ | 実装済み | `frontend/src/mocks/handlers.ts` |

## チケット詳細

### チケット情報
- **ファイル名**: `gui-files-add-button`
- **説明**: Files画面 - Addボタン機能実装
- **優先度**: 9
- **タグ**: `gui, frontend, files`

### 仕様
- Add ボタンクリック時にパス入力ダイアログを表示
- ユーザーがファイルパスを入力して追加
- `useCreateFile` mutation を使用してAPIを呼び出し

### タスク
1. `AddFileDialog` コンポーネントの作成（パス入力フォーム）
2. FilesPage に Add ボタンの onClick ハンドラを追加
3. ダイアログから `useCreateFile` mutation を呼び出し
4. テストの追加
5. 静的解析・テスト実行

### 修正対象ファイル
- `frontend/src/pages/FilesPage.tsx`
- `frontend/src/components/dialogs/AddFileDialog.tsx` (新規作成)

## 実行手順

1. ticket スキルを使用してチケットを作成:
```bash
/ticket create gui-files-add-button "Files画面 - Addボタン機能実装" 9 gui,frontend,files
```

2. 作成されたチケットファイルを編集して詳細タスクを追加
