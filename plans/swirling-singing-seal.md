# GUI Frontend Projects & Files 実装計画

## チケット概要

`tickets/260124-164016-gui-frontend-projects-files.md`

プロジェクト一覧画面（ホーム）、プロジェクト作成/複製/削除ダイアログ、Filesタブ、Document Viewerを実装。TDDワークフローに従う。

**スコープ**: バックエンドAPI + フロントエンド両方を実装

---

## Step 1: バックエンド API 実装

プロジェクト管理用のAPIルーター（`/api/projects`）を新規作成:

### 新規ファイル

1. **`src/genglossary/api/schemas/project_schemas.py`**
   - `ProjectResponse` - プロジェクト情報レスポンス
   - `ProjectCreateRequest` - 作成リクエスト
   - `ProjectCloneRequest` - 複製リクエスト
   - `ProjectUpdateRequest` - 更新リクエスト

2. **`src/genglossary/api/routers/projects.py`**
   ```
   GET    /api/projects              - 一覧取得
   GET    /api/projects/{id}         - 個別取得
   POST   /api/projects              - 作成
   POST   /api/projects/{id}/clone   - 複製
   DELETE /api/projects/{id}         - 削除
   PATCH  /api/projects/{id}         - 更新
   ```

3. **更新**: `routers/__init__.py`, `app.py` にルーター登録

---

## フロントエンド実装

### Phase 1: Red（テスト作成）

**新規ファイル**: `frontend/src/__tests__/projects-page.test.tsx`

```typescript
// テストシナリオ:
describe('HomePage (Projects)', () => {
  it('ローディング状態を表示')
  it('空状態（プロジェクトなし）を表示')
  it('プロジェクト一覧を統計付きで表示')
  it('クリックでプロジェクト選択')
  it('選択プロジェクトのサマリーカード表示')
})

describe('Create/Clone/Delete Dialogs', () => {
  it('作成ダイアログのバリデーション')
  it('API呼び出しとトースト通知')
})

describe('FilesPage', () => {
  it('ファイル一覧表示')
  it('diff-scan実行')
  it('Document Viewerへの遷移')
})
```

**MSWハンドラー**: `frontend/src/mocks/handlers.ts`

### Phase 2: 型定義とHooks

**更新**: `frontend/src/api/types.ts`
```typescript
export type ProjectStatus = 'created' | 'running' | 'completed' | 'error'

export interface ProjectResponse {
  id: number
  name: string
  doc_root: string
  llm_provider: string
  llm_model: string
  created_at: string
  updated_at: string
  last_run_at: string | null
  status: ProjectStatus
}

export interface DiffScanResponse {
  added: string[]
  modified: string[]
  deleted: string[]
}
```

**新規**: `frontend/src/api/hooks/useProjects.ts`
- `useProjects()` - 一覧取得
- `useProject(id)` - 個別取得
- `useCreateProject()` - 作成 mutation
- `useCloneProject()` - 複製 mutation
- `useDeleteProject()` - 削除 mutation

**新規**: `frontend/src/api/hooks/useFiles.ts`
- `useFiles(projectId)` - ファイル一覧
- `useCreateFile()` - 追加 mutation
- `useDeleteFile()` - 削除 mutation
- `useDiffScan()` - スキャン mutation

### Phase 3: Green（ページ実装）

**新規ページコンポーネント**:

1. **`frontend/src/pages/HomePage.tsx`**
   - 左: プロジェクトリスト（選択可能）
   - 右: 選択プロジェクトのサマリーカード
   - [+ Create] ボタン → ダイアログ

2. **`frontend/src/pages/FilesPage.tsx`**
   - ファイルリスト（Table）
   - [Scan] [+ Add] ボタン
   - 行クリック → Document Viewer

3. **`frontend/src/pages/DocumentViewerPage.tsx`**
   - タブ式ドキュメント表示
   - 右: 用語カード（placeholder）

**ダイアログコンポーネント**:

4. **`frontend/src/components/dialogs/CreateProjectDialog.tsx`**
5. **`frontend/src/components/dialogs/CloneProjectDialog.tsx`**
6. **`frontend/src/components/dialogs/DeleteProjectDialog.tsx`**

### Phase 4: ルーティング更新

**更新**: `frontend/src/routes/index.tsx`

```typescript
// プロジェクトIDをURLパラメータで管理
'/'                              → HomePage
'/projects/:projectId/files'     → FilesPage
'/projects/:projectId/document-viewer' → DocumentViewerPage
```

---

## 依存関係図

```
Backend projects router (前提条件)
    │
    ├──▶ types.ts (Project型追加)
    │         │
    │         ├──▶ MSW handlers → Tests (Red)
    │         │
    │         └──▶ TanStack Query hooks
    │                   │
    │                   └──▶ Pages (Green)
    │                             │
    │                             └──▶ Routing
```

---

## 重要ファイル

| 目的 | ファイルパス |
|------|-------------|
| バックエンドルーターパターン | `src/genglossary/api/routers/files.py` |
| プロジェクトリポジトリ | `src/genglossary/db/project_repository.py` |
| フロントエンド型定義 | `frontend/src/api/types.ts` |
| MSWセットアップ | `frontend/src/__tests__/setup.ts` |
| ルーティング設定 | `frontend/src/routes/index.tsx` |
| テストパターン | `frontend/src/__tests__/app-shell.test.tsx` |

---

## 使用するMantineコンポーネント

- `Table` - ファイル/プロジェクトリスト
- `Card` - サマリーカード
- `Modal` - ダイアログ
- `TextInput`, `Select` - フォーム
- `Skeleton` - ローディング
- `Badge` - ステータス表示
- `Tabs` - Document Viewer
- `@mantine/notifications` - トースト通知（追加が必要）

---

## 検証方法

1. **テスト実行**: `cd frontend && npm run test`
2. **ビルド確認**: `cd frontend && npm run build`
3. **バックエンドテスト**: `uv run pytest`
4. **静的解析**: `uv run pyright`
5. **E2E確認**: 開発サーバー起動してブラウザで動作確認
