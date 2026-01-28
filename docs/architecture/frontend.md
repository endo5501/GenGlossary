# フロントエンド層（React SPA）

React + TypeScript で構築されたシングルページアプリケーション（SPA）です。バックエンドの FastAPI と連携し、用語集生成の各ステップを GUI で管理します。

## 技術スタック

| カテゴリ | 技術 | バージョン |
|---------|-----|-----------|
| フレームワーク | React | 19.2 |
| 言語 | TypeScript | 5.9 |
| ビルドツール | Vite | 7.2 |
| UIライブラリ | Mantine | 8.3 |
| 通知 | @mantine/notifications | 8.3 |
| ファイルドロップ | @mantine/dropzone | 8.3 |
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
import { Notifications } from '@mantine/notifications'
import '@mantine/notifications/styles.css'

// MantineProvider + RouterProvider + Notifications でアプリをラップ
<MantineProvider theme={theme}>
  <Notifications />
  <RouterProvider router={router} />
</MantineProvider>
```

### テーマ設定（theme/theme.ts）

Mantine のデフォルトテーマをベースにカスタマイズ。

## コンポーネント設計

### レイアウトコンポーネント（components/layout/）

| コンポーネント | 説明 |
|---------------|------|
| `AppShell` | メインレイアウト。`projectId`の有無に応じて表示要素を切り替え |
| `GlobalTopBar` | グローバルヘッダー。ホーム画面ではシンプル表示、プロジェクト詳細では完全表示 |
| `LeftNavRail` | 左サイドナビゲーション。プロジェクト詳細画面でのみ表示 |
| `LogPanel` | 折りたたみ可能なログビューア。プロジェクト詳細画面でのみ表示 |

#### AppShell レイアウト

**レイアウト分離:**
- ホーム画面（`/`）: シンプルレイアウト（ヘッダーのみ）
- プロジェクト詳細画面（`/projects/$projectId/*`）: フルレイアウト

**ホーム画面レイアウト:**
```
┌────────────────────────────────────────────────┐
│     GlobalTopBar (シンプル: タイトルのみ)       │
├────────────────────────────────────────────────┤
│                                                │
│              Content Area                      │
│             (プロジェクト一覧)                  │
│                                                │
└────────────────────────────────────────────────┘
```

**プロジェクト詳細画面レイアウト:**
```
┌────────────────────────────────────────────────┐
│  GlobalTopBar (戻る + タイトル + ステータス + Run/Stop) │
├────────────┬───────────────────────────────────┤
│            │                                   │
│ LeftNavRail│         Content Area              │
│  (200px)   │        (Outlet)                   │
│            │                                   │
│            ├───────────────────────────────────┤
│            │   LogPanel (折りたたみ可能)        │
└────────────┴───────────────────────────────────┘
```

**条件付きレンダリング:**
```typescript
const hasProject = projectId !== undefined

// ナビゲーションバーはプロジェクト詳細のみ
navbar={hasProject ? { width: 200, breakpoint: 'sm' } : undefined}

// LeftNavRailはプロジェクト詳細のみ
{hasProject && <MantineAppShell.Navbar>...</MantineAppShell.Navbar>}

// LogPanelはプロジェクト詳細のみ
{hasProject && <LogPanel projectId={projectId} runId={runId} />}
```

#### GlobalTopBar の機能

**ホーム画面（`projectId === undefined`）:**
- **アプリタイトル**: "GenGlossary" のみ表示

**プロジェクト詳細画面（`projectId !== undefined`）:**
- **戻るボタン**: ホーム画面に戻るための `Back` ボタン（左矢印アイコン付き）
- **アプリタイトル**: "GenGlossary"（クリック可能でホーム画面に遷移）
- **パイプラインステータス**: 現在の実行状態をバッジで表示
- **進捗表示**: 実行中は `current / total` を表示
- **Run ボタン**: パイプライン実行開始（実行中または開始処理中は無効化）
- **Stop ボタン**: 実行中のパイプラインをキャンセル（非実行中または `runId` 未取得時は無効化）
- **Scope セレクター**: 実行範囲の選択（Full Pipeline / From Terms / Provisional to Refined）

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
| `FilesPage` | ファイル一覧と追加・削除 |
| `TermsPage` | 抽出された用語一覧と詳細表示 |
| `ProvisionalPage` | 暫定用語集の表示と編集 |
| `IssuesPage` | 精査で見つかった問題一覧 |
| `RefinedPage` | 最終用語集の表示とエクスポート |
| `DocumentViewerPage` | ドキュメント閲覧ページ |
| `SettingsPage` | プロジェクト設定ページ（名前、LLM設定の編集） |

#### 用語集関連ページの共通パターン

**ID ベースの選択:**
```typescript
// オブジェクトを直接保存するのではなく、ID を保存
const [selectedId, setSelectedId] = useState<number | null>(null)
const selectedEntry = entries?.find((e) => e.id === selectedId) ?? null
```

**キーボードアクセシビリティ:**
```typescript
<Table.Tr
  onClick={() => setSelectedId(entry.id)}
  onKeyDown={(e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      setSelectedId(entry.id)
    }
  }}
  tabIndex={0}
  role="button"
  aria-selected={selectedId === entry.id}
  style={{ cursor: 'pointer' }}
>
```

**設計ポイント:**
- IDベースの選択により、データ更新時に自動的に最新の値が反映される
- キーボード操作（Tab + Enter/Space）をサポート
- ARIA属性でスクリーンリーダー対応

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

#### AddFileDialog の Dropzone UI

@mantine/dropzone を使用したファイルアップロードダイアログ。HTML5 File API でファイル内容を読み取り、バックエンドに送信。

```typescript
// Dropzone設定
<Dropzone
  onDrop={handleDrop}
  accept={['text/markdown', 'text/plain']}
  maxSize={5 * 1024 * 1024}  // 5MB制限
>
  ...
</Dropzone>

// FileReader APIでファイル内容を読み取り
const handleDrop = (files: FileWithPath[]) => {
  files.forEach((file) => {
    const reader = new FileReader()
    reader.onload = () => {
      // ファイル名と内容をstateに保存
    }
    reader.readAsText(file)
  })
}

// 一括アップロード
const handleAdd = () => {
  createFilesBulk(
    selectedFiles.map((f) => ({ file_name: f.name, content: f.content }))
  )
}
```

**UI構成:**
```
┌─────────────────────────────────────┐
│  Add Files                      [×] │
├─────────────────────────────────────┤
│  ┌─────────────────────────────┐    │
│  │   Drag files here or click  │    │
│  │   to select                 │    │
│  │   Only .txt and .md files   │    │
│  └─────────────────────────────┘    │
│  Selected Files (2)                 │
│  ├─ document1.md         [Remove]   │
│  └─ notes.txt            [Remove]   │
│            [Cancel]  [Add (2)]      │
└─────────────────────────────────────┘
```

### ダイアログコンポーネント（components/dialogs/）

| コンポーネント | 説明 |
|---------------|------|
| `CreateProjectDialog` | 新規プロジェクト作成ダイアログ |
| `CloneProjectDialog` | プロジェクトクローンダイアログ |
| `DeleteProjectDialog` | プロジェクト削除確認ダイアログ |
| `AddFileDialog` | ファイル追加ダイアログ（@mantine/dropzone使用、複数ファイル対応） |

#### CreateProjectDialog の設計

```typescript
// LLM Provider は Select コンポーネントで選択
const LLM_PROVIDERS = [
  { value: 'ollama', label: 'Ollama' },
  { value: 'openai', label: 'OpenAI' },
]

// フォームフィールド
// - Project Name: TextInput (必須)
// - LLM Provider: Select (デフォルト: ollama)
// - LLM Model: TextInput
// - Base URL: TextInput (OpenAI選択時のみ表示)
//
// NOTE: Document Rootはバックエンドで自動生成されるため、入力欄はありません
```

**設計ポイント:**
- LLM Provider は入力ミス防止のため Select コンポーネントを使用
- SettingsPage と同じ `LLM_PROVIDERS` 定数を使用（将来的には共通化を検討）
- Base URL は OpenAI 選択時のみ条件付き表示（SettingsPage と同様のパターン）
- Document Root はバックエンドで `{data_dir}/projects/{project_name}/` に自動生成される

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
| `PageContainer` | ページ共通のローディング、エラー、空状態を処理するコンテナ |
| `OccurrenceList` | 用語の出現箇所リストを表示 |

#### PageContainer

ページ共通のローディング、エラー、空状態をハンドリングするコンテナコンポーネント。

```typescript
interface PageContainerProps {
  isLoading: boolean       // ローディング中かどうか
  isEmpty: boolean         // データが空かどうか
  emptyMessage: string     // 空状態のメッセージ
  actionBar: ReactNode     // アクションボタン領域
  children: ReactNode      // コンテンツ
  loadingTestId?: string   // ローディング状態のテスト用ID
  emptyTestId?: string     // 空状態のテスト用ID
  error?: Error | null     // エラーオブジェクト
  onRetry?: () => void     // リトライ時のコールバック
}
```

**状態遷移:**
1. `isLoading: true` → ローディングスピナー表示
2. `error` が存在 → エラーメッセージとリトライボタン表示
3. `isEmpty: true` → 空状態メッセージ表示
4. それ以外 → `children` を表示

#### OccurrenceList

用語の出現箇所をカードリストで表示。

```typescript
interface Occurrence {
  document_path: string  // ドキュメントパス
  line_number: number    // 行番号
  context: string        // 前後のコンテキスト
}

// キーには安定した一意の値を使用
key={`${occ.document_path}:${occ.line_number}`}

## APIクライアント（api/）

### client.ts

fetch ベースの軽量 HTTP クライアント。

```typescript
// ベースURL取得（他のモジュールからも利用可能）
export function getBaseUrl(): string

export const apiClient = {
  get: <T>(endpoint: string): Promise<T>,
  post: <T>(endpoint: string, data?: unknown): Promise<T>,
  put: <T>(endpoint: string, data?: unknown): Promise<T>,
  patch: <T>(endpoint: string, data?: unknown): Promise<T>,
  delete: <T>(endpoint: string): Promise<T>,
}
```

#### getBaseUrl

環境に応じたAPIベースURLを返す関数。SSEなど`apiClient`を経由しない通信でも使用。

```typescript
export function getBaseUrl(): string {
  const envUrl = import.meta.env.VITE_API_BASE_URL
  if (!envUrl || envUrl === 'undefined') {
    return 'http://localhost:8000'
  }
  return envUrl
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
| `FileResponse` | ファイル情報（id, file_name, content_hash） |
| `TermResponse` | 抽出された用語（id, term_text, category） |
| `TermOccurrence` | 用語の出現箇所（line_number, context） |
| `GlossaryTermResponse` | 用語集エントリ（term_name, definition, confidence, occurrences） |
| `IssueResponse` | 精査で見つかった問題（issue_type, description, severity） |
| `RunResponse` | パイプライン実行状態（scope, status, progress, timestamps） |
| `SettingsResponse` | 設定（model_name, ollama_base_url, max_retries, timeout_seconds） |
| `PaginatedResponse<T>` | ページネーション付きレスポンス |
| `ErrorResponse` | エラーレスポンス |

### hooks/

TanStack Query を使用したカスタムフック。

#### データフェッチフック

| フック | 説明 |
|-------|------|
| `useTerms` | 用語一覧を取得 |
| `useProvisional` | 暫定用語集を取得 |
| `useIssues` | 問題一覧を取得（issueType でフィルタ可能） |
| `useRefined` | 最終用語集を取得 |
| `useCurrentRun` | 現在の実行状態を取得 |

```typescript
// 例: useTerms
export const useTerms = (projectId: number) =>
  useQuery(['terms', projectId], () => apiClient.get<TermResponse[]>(`/api/projects/${projectId}/terms`))
```

#### ミューテーションフック

| フック | 説明 |
|-------|------|
| `useExtractTerms` | 用語抽出を実行 |
| `useCreateTerm` / `useDeleteTerm` | 用語の追加/削除 |
| `useUpdateProvisional` | 暫定用語集エントリを更新 |
| `useRegenerateProvisional` | 暫定用語集を再生成 |
| `useReviewIssues` | 問題精査を実行 |
| `useRegenerateRefined` | 最終用語集を再生成 |
| `useExportMarkdown` | Markdown 形式でエクスポート |

#### useLogStream

SSE（Server-Sent Events）を使用したログストリーミングフック。

```typescript
interface UseLogStreamResult {
  logs: LogMessage[]      // ログメッセージ配列
  isConnected: boolean    // 接続状態
  error: Error | null     // エラー
  clearLogs: () => void   // ログクリア
}

export function useLogStream(
  projectId: number,
  runId: number | undefined
): UseLogStreamResult
```

**設計ポイント:**
- `getBaseUrl()` を使用して環境に応じた URL を生成
- `runId` 変更時に自動でログをクリア
- メモリリーク防止のため最大1000件に制限
- クリーンアップ時に `EventSource.close()` を呼び出し

## ユーティリティ（utils/）

### colors.ts

ステータスや重要度に応じた色定義とヘルパー関数。

```typescript
// 型定義
export type RunStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
export type Severity = 'low' | 'medium' | 'high'
export type IssueType = 'ambiguous' | 'inconsistent' | 'missing'

// 色マッピング
export const statusColors: Record<RunStatus, string>
export const severityColors: Record<Severity, string>
export const issueTypeColors: Record<IssueType, string>
export const levelColors: Record<string, string>  // ログレベル用

// ヘルパー関数（型安全でデフォルト値付き）
export function getStatusColor(status: string): string
export function getSeverityColor(severity: string): string
export function getIssueTypeColor(issueType: string): string
```

**設計ポイント:**
- 厳密な型定義で不正な値を防止
- ヘルパー関数で未知の値に対してデフォルト色（'gray'）を返す
- Mantine の色名を使用

## ルーティング（routes/）

TanStack Router を使用した型安全なルーティング。

### ルート一覧

**プロジェクト一覧:**
| パス | ページ | 説明 |
|-----|-------|------|
| `/` | Home | プロジェクト一覧とサマリー |

**プロジェクトスコープルート（`/projects/$projectId/...`）:**
| パス | ページ | 説明 |
|-----|-------|------|
| `/projects/$projectId/files` | Files | 登録ファイル一覧 |
| `/projects/$projectId/document-viewer` | Document Viewer | ドキュメント閲覧 |
| `/projects/$projectId/settings` | Settings | プロジェクト設定（名前、LLM設定） |

**レガシープレースホルダールート:**
| パス | ページ | 説明 |
|-----|-------|------|
| `/files` | Files | 登録ファイル一覧（プレースホルダー） |
| `/terms` | Terms | 抽出された用語一覧 |
| `/provisional` | Provisional Glossary | 暫定用語集 |
| `/issues` | Issues | 精査結果（問題点）一覧 |
| `/refined` | Refined Glossary | 最終用語集 |
| `/document-viewer` | Document Viewer | ドキュメント閲覧 |
| `/settings` | Settings | 設定ページ（プレースホルダー） |

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

### テストセットアップ（setup.ts）

テスト環境で必要なモックを `src/__tests__/setup.ts` で設定：

- **matchMedia**: Mantine UIコンポーネント用
- **ResizeObserver**: レイアウト監視用
- **scrollIntoView**: Mantine Combobox用
- **EventSource**: SSEログストリーミング用

### テストファイル構成

| ファイル | テスト数 | 対象 |
|---------|---------|------|
| `api-client.test.ts` | 14 | APIクライアントの HTTP メソッド、エラーハンドリング |
| `app-shell.test.tsx` | 32 | AppShell、GlobalTopBar（戻るボタン含む）、LeftNavRail、LogPanel、レイアウト分離 |
| `routing.test.tsx` | 16 | ルーティング、ナビゲーション |
| `projects-page.test.tsx` | 16 | HomePage、FilesPage、ダイアログコンポーネント |
| `components/dialogs/AddFileDialog.test.tsx` | 6 | AddFileDialogコンポーネント |
| `settings-page.test.tsx` | 11 | SettingsPage（フォーム、バリデーション、API連携） |
| `terms-workflow.test.tsx` | 43 | Terms/Provisional/Issues/Refined ページ、Run管理、LogPanel |

**合計**: 138 テスト

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
| Files ページ | `GET/POST/POST(bulk)/DELETE /api/projects/{project_id}/files` |
| Terms ページ | `GET /api/projects/{project_id}/terms` |
| Provisional ページ | `GET /api/projects/{project_id}/provisional` |
| Issues ページ | `GET /api/projects/{project_id}/issues` |
| Refined ページ | `GET /api/projects/{project_id}/refined` |
| Run/Stop ボタン | `POST/DELETE /api/projects/{project_id}/runs` |
| Settings ページ | `GET/PATCH /api/projects/{project_id}` |

### 環境変数

| 変数名 | 説明 | デフォルト |
|-------|------|-----------|
| `VITE_API_BASE_URL` | バックエンド API のベース URL | `http://localhost:8000` |

## 関連ドキュメント

- [API](./api.md) - バックエンド API 仕様
- [Run管理](./runs.md) - パイプライン実行管理
- [ディレクトリ構成](./directory-structure.md) - プロジェクト全体構造
