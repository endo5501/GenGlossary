# フロントエンド層（React SPA）

React + TypeScript で構築されたシングルページアプリケーション（SPA）です。バックエンドの FastAPI と連携し、用語集生成の各ステップを GUI で管理します。

## 技術スタック

| カテゴリ | 技術 | バージョン |
|---------|-----|-----------|
| フレームワーク | React | 19.2 |
| 言語 | TypeScript | 5.9 |
| ビルドツール | Vite | 7.2 |
| UIライブラリ | Mantine | 8.3 |
| アイコン | Tabler Icons | 3.36 |
| ルーティング | TanStack Router | 1.x |
| データフェッチ | TanStack Query | 5.x |
| テスト | Vitest + RTL + MSW | - |

## アプリケーション構造

```
frontend/src/
├── main.tsx              # エントリーポイント
├── theme/theme.ts        # Mantineテーマ設定
├── api/                  # API通信層
├── components/           # Reactコンポーネント
└── routes/               # ルーティング設定
```

### エントリーポイント（main.tsx）

```tsx
// MantineProvider + RouterProvider でアプリをラップ
<MantineProvider theme={theme}>
  <RouterProvider router={router} />
</MantineProvider>
```

### テーマ設定（theme/theme.ts）

Mantine のデフォルトテーマをベースにカスタマイズ。

## コンポーネント設計

### レイアウトコンポーネント（components/layout/）

| コンポーネント | 説明 |
|---------------|------|
| `AppShell` | メインレイアウト。ヘッダー (60px)、ナビゲーション (200px)、コンテンツエリアを含む |
| `GlobalTopBar` | グローバルヘッダー。アプリタイトル、パイプラインステータス、Run/Stop ボタン |
| `LeftNavRail` | 左サイドナビゲーション。8ページへのリンク |
| `LogPanel` | 折りたたみ可能なログビューア。パイプライン実行ログを表示 |

#### AppShell レイアウト

```
┌────────────────────────────────────────────────┐
│           GlobalTopBar (60px)                  │
├────────────┬───────────────────────────────────┤
│            │                                   │
│ LeftNavRail│         Content Area              │
│  (200px)   │        (Outlet)                   │
│            │                                   │
│            ├───────────────────────────────────┤
│            │   LogPanel (折りたたみ可能)        │
└────────────┴───────────────────────────────────┘
```

#### GlobalTopBar の機能

- **アプリタイトル**: "GenGlossary"
- **パイプラインステータス**: 現在の実行状態を表示
- **Run ボタン**: パイプライン実行開始（未実装 → API 連携予定）
- **Stop ボタン**: 実行中のパイプラインをキャンセル（未実装 → API 連携予定）

#### LeftNavRail のナビゲーション項目

| パス | アイコン | ラベル |
|-----|---------|-------|
| `/` | IconHome | Home |
| `/files` | IconFiles | Files |
| `/terms` | IconList | Terms |
| `/provisional` | IconBook | Provisional |
| `/issues` | IconAlertTriangle | Issues |
| `/refined` | IconBookmark | Refined |
| `/document-viewer` | IconFileText | Documents |
| `/settings` | IconSettings | Settings |

### ページコンポーネント（pages/）

| コンポーネント | 説明 |
|---------------|------|
| `HomePage` | プロジェクト一覧とサマリー表示 |
| `FilesPage` | ファイル一覧とdiff-scan結果表示 |

#### HomePage のユーティリティ関数

```typescript
function formatLastRun(lastRunAt: string | null, format: 'short' | 'long' = 'short'): string {
  if (!lastRunAt) return format === 'short' ? '-' : 'Never'
  const date = new Date(lastRunAt)
  return format === 'short' ? date.toLocaleDateString() : date.toLocaleString()
}
```

**設計ポイント:**
- 日付フォーマットを統一し、テーブル（short）とサマリーカード（long）で異なる形式を使用
- null値のハンドリングもフォーマットに応じて変更（"-" または "Never"）

#### FilesPage の ChangeSection コンポーネント

diff-scan 結果の表示で Added/Modified/Deleted セクションの重複を排除。

```typescript
interface ChangeSectionProps {
  items: string[]
  label: string
  color: string
  prefix: string
}

function ChangeSection({ items, label, color, prefix }: ChangeSectionProps) {
  if (items.length === 0) return null

  return (
    <Box>
      <Group gap="xs" mb="xs">
        <Badge color={color} size="sm">{label}</Badge>
        <Text size="sm" c="dimmed">({items.length} files)</Text>
      </Group>
      <Stack gap={4}>
        {items.map((path) => (
          <Text key={path} size="sm" c={color}>
            {prefix} {path}
          </Text>
        ))}
      </Stack>
    </Box>
  )
}

// 使用例（DiffScanResults内）
const sections = [
  { items: results.added, label: 'Added', color: 'green', prefix: '+' },
  { items: results.modified, label: 'Modified', color: 'yellow', prefix: '~' },
  { items: results.deleted, label: 'Deleted', color: 'red', prefix: '-' },
]

{sections.map((section) => (
  <ChangeSection key={section.label} {...section} />
))}
```

### ダイアログコンポーネント（components/dialogs/）

| コンポーネント | 説明 |
|---------------|------|
| `CreateProjectDialog` | 新規プロジェクト作成ダイアログ |
| `CloneProjectDialog` | プロジェクトクローンダイアログ |
| `DeleteProjectDialog` | プロジェクト削除確認ダイアログ |

#### CloneProjectDialog の設計

```typescript
// useEffectでダイアログ開閉時に状態リセット
useEffect(() => {
  if (opened) {
    setNewName(`${project.name} (Copy)`)
    setError(null)
  }
}, [opened, project.name])  // project.nameを依存配列に指定

// handleCloseは単純にonCloseを呼ぶだけ（リセットはuseEffectで行う）
const handleClose = () => {
  onClose()
}
```

**設計ポイント:**
- `useEffect`の依存配列には実際に使用している値（`project.name`）を指定
- `handleClose`での状態リセットは`useEffect`と重複するため削除

### 共通コンポーネント（components/common/）

| コンポーネント | 説明 |
|---------------|------|
| `PagePlaceholder` | 未実装ページ用のプレースホルダー。タイトルを表示 |

## APIクライアント（api/）

### client.ts

fetch ベースの軽量 HTTP クライアント。

```typescript
export const apiClient = {
  get: <T>(endpoint: string): Promise<T>,
  post: <T>(endpoint: string, data?: unknown): Promise<T>,
  put: <T>(endpoint: string, data?: unknown): Promise<T>,
  patch: <T>(endpoint: string, data?: unknown): Promise<T>,
  delete: <T>(endpoint: string): Promise<T>,
}
```

#### ApiError クラス

```typescript
export class ApiError extends Error {
  status: number      // HTTPステータスコード
  detail?: string     // エラー詳細メッセージ
}
```

#### 設定

- ベースURL: `VITE_API_BASE_URL` 環境変数、またはデフォルト `http://localhost:8000`
- Content-Type: JSON リクエストには自動的に `application/json` を設定

### types.ts

API レスポンスの TypeScript 型定義。

| 型 | 説明 |
|---|------|
| `FileResponse` | ファイル情報（id, file_path, content_hash） |
| `TermResponse` | 抽出された用語（id, term_text, category） |
| `TermOccurrence` | 用語の出現箇所（line_number, context） |
| `GlossaryTermResponse` | 用語集エントリ（term_name, definition, confidence, occurrences） |
| `IssueResponse` | 精査で見つかった問題（issue_type, description, severity） |
| `RunResponse` | パイプライン実行状態（scope, status, progress, timestamps） |
| `SettingsResponse` | 設定（model_name, ollama_base_url, max_retries, timeout_seconds） |
| `PaginatedResponse<T>` | ページネーション付きレスポンス |
| `ErrorResponse` | エラーレスポンス |

### hooks/（将来実装）

TanStack Query を使用したカスタムフック。

```typescript
// 例: useTerms, useProvisionalGlossary, useRun など
export const useTerms = (projectId: number) =>
  useQuery(['terms', projectId], () => apiClient.get<TermResponse[]>(`/api/projects/${projectId}/terms`))
```

## ルーティング（routes/）

TanStack Router を使用した型安全なルーティング。

### ルート一覧

| パス | ページ | 説明 |
|-----|-------|------|
| `/` | Home | ダッシュボード（未実装） |
| `/files` | Files | 登録ファイル一覧 |
| `/terms` | Terms | 抽出された用語一覧 |
| `/provisional` | Provisional Glossary | 暫定用語集 |
| `/issues` | Issues | 精査結果（問題点）一覧 |
| `/refined` | Refined Glossary | 最終用語集 |
| `/document-viewer` | Document Viewer | ドキュメント閲覧 |
| `/settings` | Settings | 設定ページ |

### ルート構成

```typescript
// Root route でレイアウト（AppShell）を適用
const rootRoute = createRootRoute({
  component: AppShell,
})

// 各ページをルートとして定義
const routes = routeConfigs.map(({ path, title }) =>
  createRoute({
    getParentRoute: () => rootRoute,
    path,
    component: () => <PagePlaceholder title={title} />,
  })
)
```

## テスト戦略

### テストフレームワーク

- **Vitest**: テストランナー
- **React Testing Library (RTL)**: コンポーネントテスト
- **MSW (Mock Service Worker)**: API モック

### テストファイル構成

| ファイル | テスト数 | 対象 |
|---------|---------|------|
| `api-client.test.ts` | 14 | APIクライアントの HTTP メソッド、エラーハンドリング |
| `app-shell.test.tsx` | 19 | AppShell、GlobalTopBar、LeftNavRail、LogPanel |
| `routing.test.tsx` | 16 | ルーティング、ナビゲーション |
| `projects-page.test.tsx` | 11 | HomePage、FilesPage、ダイアログコンポーネント |

**合計**: 60 テスト

### テスト実行

```bash
pnpm test        # テスト実行
pnpm test:watch  # ウォッチモード
```

## 開発コマンド

```bash
# 開発サーバー起動（ホットリロード）
pnpm dev

# プロダクションビルド
pnpm build

# テスト実行
pnpm test

# リント
pnpm lint
```

## バックエンドとの連携

### API エンドポイント対応

| フロントエンド | バックエンド API |
|---------------|-----------------|
| Files ページ | `GET /api/projects/{project_id}/files` |
| Terms ページ | `GET /api/projects/{project_id}/terms` |
| Provisional ページ | `GET /api/projects/{project_id}/provisional` |
| Issues ページ | `GET /api/projects/{project_id}/issues` |
| Refined ページ | `GET /api/projects/{project_id}/refined` |
| Run/Stop ボタン | `POST/DELETE /api/projects/{project_id}/runs` |
| Settings ページ | `GET/PUT /api/settings`（未実装） |

### 環境変数

| 変数名 | 説明 | デフォルト |
|-------|------|-----------|
| `VITE_API_BASE_URL` | バックエンド API のベース URL | `http://localhost:8000` |

## 関連ドキュメント

- [API](./api.md) - バックエンド API 仕様
- [Run管理](./runs.md) - パイプライン実行管理
- [ディレクトリ構成](./directory-structure.md) - プロジェクト全体構造
