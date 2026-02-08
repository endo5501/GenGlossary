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
| 状態管理 | Zustand | 5.x |
| テスト | Vitest + RTL + MSW | - |

## アプリケーション構造

```
frontend/src/
├── main.tsx              # エントリーポイント
├── theme/theme.ts        # Mantineテーマ設定
├── styles/               # 共通スタイル
│   └── layout.css        # レイアウト用CSSクラスと変数
├── api/                  # API通信層
├── components/           # Reactコンポーネント
├── constants/            # 共通定数
│   └── llm.ts            # LLM関連の定数（プロバイダー、デフォルトURL）
├── hooks/                # カスタムフック
├── utils/                # ユーティリティ関数
│   └── getRowSelectionProps.ts # 行選択ロジックのprops生成
├── store/                # Zustand 状態管理
│   └── logStore.ts       # ログと進捗の状態管理
└── routes/               # ルーティング設定
```

### エントリーポイント（main.tsx）

```tsx
import { Notifications } from '@mantine/notifications'
import '@mantine/notifications/styles.css'
import './styles/layout.css'  // 共通レイアウトスタイル

// MantineProvider + RouterProvider + Notifications でアプリをラップ
<MantineProvider theme={theme}>
  <Notifications />
  <RouterProvider router={router} />
</MantineProvider>
```

### 共通スタイル（styles/layout.css）

レイアウト用の CSS クラスと CSS 変数を定義します。

```css
:root {
  --header-height: 60px;  /* グローバルヘッダーの高さ */
}

.page-layout { height: 100%; display: flex; flex-direction: column; }
.scrollable-content { flex: 1; overflow-y: auto; min-height: 0; }
.action-bar { flex-shrink: 0; border-bottom: 1px solid var(--mantine-color-gray-3); }

/* リストと詳細パネルの左右分割レイアウト */
.split-layout { display: flex; gap: var(--mantine-spacing-md); height: 100%; min-height: 0; }
.split-layout-list, .split-layout-detail { overflow-y: auto; min-height: 0; }
.split-layout-list { flex: 1; }
.split-layout-detail { flex: 0 0 40%; }

@media (max-width: 768px) {
  .split-layout { flex-direction: column; }
  .split-layout-detail { flex: none; }
}
```

**CSS変数の使用:**
- `--header-height`: AppShell や DocumentViewerPage で高さ計算に使用

### テーマ設定（theme/theme.ts）

Mantine のデフォルトテーマをベースにカスタマイズ。

## コンポーネント設計

### レイアウトコンポーネント（components/layout/）

| コンポーネント | 説明 |
|---------------|------|
| `AppShell` | メインレイアウト。`projectId`の有無に応じて表示要素を切り替え |
| `GlobalTopBar` | グローバルヘッダー。ホーム画面ではシンプル表示、プロジェクト詳細では完全表示 |
| `LeftNavRail` | 左サイドナビゲーション。プロジェクト詳細画面でのみ表示 |
| `LogPanel` | 折りたたみ可能なログビューア。進捗バー表示機能付き。プロジェクト詳細画面でのみ表示 |

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
│            │   ActionBar (固定)                │
│            ├───────────────────────────────────┤
│ LeftNavRail│                                   │
│  (200px)   │   Content Area (スクロール可能)    │
│            │                                   │
│            ├───────────────────────────────────┤
│            │   LogPanel (固定、折りたたみ可能)  │
└────────────┴───────────────────────────────────┘
```

**3層固定レイアウト:**
コンテンツエリアが長くなっても ActionBar と LogPanel は常に表示されます。
- **ActionBar**: 各ページの操作ボタン（Extract, Add等）を固定表示
- **Content Area**: リストやテーブルがスクロール
- **LogPanel**: ログと進捗バーを固定表示

**条件付きレンダリング:**
```typescript
const hasProject = projectId !== undefined

// ナビゲーションバーはプロジェクト詳細のみ
navbar={hasProject ? { width: 200, breakpoint: 'sm' } : undefined}

// LeftNavRailはプロジェクト詳細のみ
{hasProject && <MantineAppShell.Navbar>...</MantineAppShell.Navbar>}

// LogPanelはプロジェクト詳細のみ
{hasProject && <LogPanel projectId={projectId} runId={runId} onRunComplete={handleRunComplete} />}
```

**Run完了時のキャッシュ無効化:**

SSEストリームの`complete`イベント発火時に、`handleRunComplete`コールバックですべてのデータリストを無効化します。これにより、Run完了後に最新のデータが自動的に表示されます。

`completedProjectId`はSSEコンテキスト（`useLogStream`）から渡されるため、ユーザーがRun中に別のプロジェクトに移動しても、正しいプロジェクトのキャッシュが無効化されます。

```typescript
const handleRunComplete = useCallback(
  (completedProjectId: number) => {
    queryClient.invalidateQueries({ queryKey: runKeys.current(completedProjectId) })
    queryClient.invalidateQueries({ queryKey: termKeys.list(completedProjectId) })
    queryClient.invalidateQueries({ queryKey: provisionalKeys.list(completedProjectId) })
    queryClient.invalidateQueries({ queryKey: issueKeys.list(completedProjectId) })
    queryClient.invalidateQueries({ queryKey: refinedKeys.list(completedProjectId) })
  },
  [queryClient]
)
```

**無効化されるクエリ:**
| クエリキー | 対応するRun scope |
|-----------|------------------|
| `runKeys.current` | すべて（現在の実行状態） |
| `termKeys.list` | extract（用語抽出） |
| `provisionalKeys.list` | generate（暫定用語集生成） |
| `issueKeys.list` | review（精査） |
| `refinedKeys.list` | refine（改善） |

#### LogPanel の進捗表示

LogPanel は Zustand ストア（`logStore`）と連携して、パイプライン実行中の進捗情報をリアルタイム表示します。

**UI構成:**
```
┌─────────────────────────────────────────────────┐
│ Logs                                    [▲/▼]   │
├─────────────────────────────────────────────────┤
│ provisional: 量子コンピュータ            5/20   │ ← 進捗情報
│ ████████████░░░░░░░░░░░░░░  25%                 │ ← アニメーションプログレスバー
├─────────────────────────────────────────────────┤
│ [INFO] 量子コンピュータ: 25%                    │
│ [INFO] キュービット: 30%                        │
│ [INFO] 重ね合わせ: 35%                          │
└─────────────────────────────────────────────────┘
```

**進捗表示の要素:**
- **ステップ名**: 現在実行中のステップ（`provisional`, `refine` など）
- **処理中の用語**: 現在処理中の用語名
- **カウント**: `current/total` 形式（例: `5/20`）
- **プログレスバー**: Mantine の `Progress` コンポーネント（アニメーション付き）

**実装:**
```typescript
// Zustand ストアから進捗情報を取得
const progress = useLogStore((state) => state.latestProgress)

// パーセンテージ計算
const progressPercent = progress && progress.total > 0
  ? Math.round((progress.current / progress.total) * 100)
  : 0

// 進捗表示（進捗データがある場合のみ表示）
{progress && (
  <Box>
    <Group justify="space-between" mb={4}>
      <Text size="xs" c="dimmed">{progress.step}: {progress.currentTerm}</Text>
      <Text size="xs" c="dimmed">{progress.current}/{progress.total}</Text>
    </Group>
    <Progress data-testid="progress-bar" value={progressPercent} size="sm" animated />
  </Box>
)}
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

#### 処理中インジケーター

パイプライン実行中、現在処理しているステップに対応するメニュー項目にスピナーを表示する。

**ステップとメニューのマッピング:**

| `current_step` | メニュー |
|----------------|----------|
| `extract` | Terms |
| `provisional` | Provisional |
| `issues` | Issues |
| `refined` | Refined |

**実装:**
- `useCurrentRun` フックで `run.status` と `run.current_step` を取得
- `status === 'running'` かつ `current_step` がマッピングに存在する場合、スピナー表示
- アクセシビリティ: `aria-busy` 属性と `aria-label="Processing"` を設定

### ページコンポーネント（pages/）

| コンポーネント | 説明 |
|---------------|------|
| `HomePage` | プロジェクト一覧とサマリー表示 |
| `FilesPage` | ファイル一覧と追加・削除 |
| `TermsPage` | 抽出された用語一覧と詳細表示、カテゴリ編集。3タブ構成（用語一覧/除外用語/必須用語） |
| `ProvisionalPage` | 暫定用語集の表示と編集 |
| `IssuesPage` | 精査で見つかった問題一覧 |
| `RefinedPage` | 最終用語集の表示とエクスポート |
| `DocumentViewerPage` | ドキュメント閲覧ページ（左右2ペイン構成） |
| `SettingsPage` | プロジェクト設定ページ（名前、LLM設定の編集） |

#### DocumentViewerPage の設計

左右2ペイン構成でドキュメント原文と用語カードを表示。

**レイアウト:**
```
┌─────────────────────────────────────────────────────────────┐
│                    Document Viewer                          │
├─────────────────────────────┬───────────────────────────────┤
│      左ペイン (60%)          │       右ペイン (40%)           │
│  ┌─────────────────────┐    │   ┌───────────────────────┐   │
│  │  ドキュメントタブ      │    │   │     用語カード         │   │
│  │  [doc1.txt] [doc2.md]│    │   │                       │   │
│  ├─────────────────────┤    │   │  用語名: ○○○          │   │
│  │                     │    │   │  定義: ...            │   │
│  │  ドキュメント本文      │    │   │  出現箇所: ...        │   │
│  │  (用語ハイライト付き)  │    │   │                       │   │
│  │                     │    │   │  [除外][編集][ジャンプ] │   │
│  └─────────────────────┘    │   └───────────────────────┘   │
└─────────────────────────────┴───────────────────────────────┘
```

**コンポーネント構成:**
- `DocumentPane`: 左ペイン（タブ + 本文表示 + 用語ハイライト）
- `TermCard`: 右ペイン（用語詳細表示）

**状態管理:**
```typescript
const [selectedFileId, setSelectedFileId] = useState<number | null>(null)
const [selectedTerm, setSelectedTerm] = useState<string | null>(null)

// ファイル切り替え時に選択用語をクリア
useEffect(() => {
  setSelectedTerm(null)
}, [selectedFileId])
```

**データ取得:**
- `useFiles(projectId)` - ファイル一覧（タブ表示用）
- `useFileDetail(projectId, fileId)` - 選択ファイルのコンテンツ
- `useRefined(projectId)` - Refined用語集（ハイライト用、優先）
- `useProvisional(projectId)` - Provisional用語集（ハイライト用、Refinedがない場合のフォールバック）

**用語ハイライトのロジック:**
- Refined用語集があればその用語のみをハイライト
- なければProvisional用語集の用語をハイライト
- COMMON_NOUNなど除外された用語はハイライトされない（用語集に含まれないため）

**用語データの優先順位:**
1. Refined があればそれを表示
2. なければ Provisional を表示
3. どちらもなければ「未定義」と表示

#### 用語集関連ページの共通パターン

**ID ベースの選択:**
```typescript
// オブジェクトを直接保存するのではなく、ID を保存
const [selectedId, setSelectedId] = useState<number | null>(null)
const selectedEntry = entries?.find((e) => e.id === selectedId) ?? null
```

**getRowSelectionProps ユーティリティ関数:**

行選択のロジック（onClick、onKeyDown、aria-selected、スタイル）を共通化するユーティリティ関数。

```typescript
// utils/getRowSelectionProps.ts
export function getRowSelectionProps<T extends { id: number }>(
  item: T,
  selectedId: number | null,
  onSelect: (id: number) => void
) {
  return {
    onClick: () => onSelect(item.id),
    onKeyDown: (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault()
        onSelect(item.id)
      }
    },
    tabIndex: 0,
    'aria-selected': selectedId === item.id,
    style: { cursor: 'pointer' },
    bg: selectedId === item.id ? 'var(--mantine-color-blue-light)' : undefined,
  }
}
```

**使用例:**
```typescript
// ProvisionalPage, RefinedPage, IssuesPage で使用
{entries?.map((entry) => (
  <Table.Tr
    key={entry.id}
    {...getRowSelectionProps(entry, selectedId, setSelectedId)}
  >
    ...
  </Table.Tr>
))}
```

**設計ポイント:**
- IDベースの選択により、データ更新時に自動的に最新の値が反映される
- キーボード操作（Tab + Enter/Space）をサポート
- ARIA属性（`aria-selected`）でスクリーンリーダー対応
- Mantine固有の`bg`プロパティで選択状態をスタイリング
- React hooksを使用していないため、hooks/ではなくutils/に配置

#### TermsPage の補足情報（user_notes）

詳細パネルに `Textarea` で補足情報を入力・自動保存する機能。

**UI構成:**
```
┌──────────────────────────────────┐
│ 用語名: 量子もつれ               │
│ カテゴリ: [Badge: 技術用語] [✏️]  │
│                                  │
│ 補足情報:                        │
│ ┌──────────────────────────────┐ │
│ │ 複数の量子ビットが相互に    │ │
│ │ 関連し合う現象。             │ │
│ └──────────────────────────────┘ │
└──────────────────────────────────┘
```

**実装:**
```typescript
// userNotesValue状態とdebounceTimerRef
const [userNotesValue, setUserNotesValue] = useState('')
const debounceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

// 自動保存（debounce 500ms）
const handleUserNotesChange = useCallback((value: string) => {
  setUserNotesValue(value)
  if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current)
  debounceTimerRef.current = setTimeout(() => {
    if (selectedTerm) {
      updateTerm.mutate({ termId: selectedTerm.id, data: { user_notes: value } })
    }
  }, 500)
}, [selectedTerm, updateTerm])

// 用語選択時にuserNotesValueを同期
const handleSelectTerm = (termId: number) => {
  setSelectedId(termId)
  const term = terms?.find((t) => t.id === termId)
  setUserNotesValue(term?.user_notes ?? '')
}
```

**機能:**
- `Textarea` による補足情報の入力（`autosize`, `minRows={3}`）
- 入力のたびに500msのdebounce後に `PATCH` APIで自動保存
- 用語選択変更時に `userNotesValue` を同期
- アンマウント時にdebounceタイマーをクリーンアップ
- LLMプロンプトに注入されることをプレースホルダーで説明

#### TermsPage のカテゴリ編集機能

詳細パネル内でカテゴリをインライン編集できる。

**UI構成:**
```
[通常表示]
  Category: [Badge: 技術用語] [✏️]

     ↓ 編集アイコンクリック

[編集モード]
  Category: [TextInput____] [✓] [✗]
```

**実装:**
```typescript
// 編集状態の管理
const [isEditingCategory, setIsEditingCategory] = useState(false)
const [editingCategoryValue, setEditingCategoryValue] = useState('')

// 選択変更時に編集状態をリセット（間違った用語のカテゴリ更新を防止）
const handleSelectTerm = (termId: number) => {
  if (termId !== selectedId) {
    resetCategoryEdit()
  }
  setSelectedId(termId)
}

// 保存処理（空文字は null として送信しカテゴリ削除）
const handleSaveCategory = () => {
  if (!selectedTerm || updateTerm.isPending) return
  const trimmedValue = editingCategoryValue.trim()
  updateTerm.mutate({
    termId: selectedTerm.id,
    data: { category: trimmedValue || null },
  })
}
```

**機能:**
- 編集アイコンクリックで編集モードに切り替え
- Enter キーで保存、Escape キーでキャンセル
- 空文字で保存するとカテゴリを削除（null に設定）
- 別の用語を選択すると自動的に編集モードを終了
- ダブルサブミット防止（`updateTerm.isPending` チェック）
- アクセシビリティ: `aria-label` 属性を設定

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
// フォームフィールド
// - Project Name: TextInput (必須)
// - LLM Settings: LlmSettingsForm コンポーネント
//   - Provider: Select (デフォルト: ollama)
//   - Base URL: TextInput
//   - Model: Select (Ollama接続時) / TextInput (それ以外)
//
// NOTE: Document Rootはバックエンドで自動生成されるため、入力欄はありません
```

**設計ポイント:**
- LLM 設定は `LlmSettingsForm` 共通コンポーネントを使用
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

### Document Viewer コンポーネント（components/document-viewer/）

| コンポーネント | 説明 |
|---------------|------|
| `DocumentPane` | 左ペイン：タブでドキュメント選択、本文表示、用語ハイライト |
| `TermCard` | 右ペイン：用語詳細（定義、出現箇所、アクションボタン） |

#### DocumentPane

ドキュメントの本文を表示し、用語をハイライトしてクリッカブルにするコンポーネント。

**主な機能:**
- ファイル一覧をタブ表示
- 選択ファイルのコンテンツ表示
- 用語のハイライト（青色背景）
- 選択中の用語のハイライト（黄色背景）
- 用語クリックで `onTermClick` コールバック呼び出し

**用語ハイライトの実装:**
```typescript
// 空の用語をフィルタリング（regex崩壊防止）
const validTerms = terms.filter((t) => t.trim().length > 0)

// 大文字小文字を無視してマッチング
const pattern = new RegExp(`(${escapedTerms.join('|')})`, 'gi')

// テキストを分割してクリッカブルなspanに変換
const parts = text.split(pattern)
```

#### TermCard

選択された用語の詳細情報を表示するコンポーネント。

**表示内容:**
- 用語名とデータソースバッジ（Refined/Provisional）
- 定義テキスト
- 出現箇所リスト（OccurrenceList使用）
- アクションボタン（除外/編集/ジャンプ）- 初期実装では disabled

**状態遷移:**
1. 用語未選択 → "Click a term in the document to view details"
2. 用語選択＆定義なし → "This term has no definition yet"
3. 用語選択＆定義あり → 詳細情報を表示

### 入力コンポーネント（components/inputs/）

| コンポーネント | 説明 |
|---------------|------|
| `LlmSettingsForm` | LLM設定フォーム（Provider, Base URL, Model） |

#### LlmSettingsForm

SettingsPage と CreateProjectDialog で共通化された LLM 設定 UI コンポーネント。

```typescript
interface LlmSettingsFormProps {
  provider: string
  model: string
  baseUrl: string
  onProviderChange: (provider: string) => void
  onModelChange: (model: string) => void
  onBaseUrlChange: (baseUrl: string) => void
  modelLabel?: string        // デフォルト: "Model"
  comboboxProps?: ComboboxProps  // テスト用
}
```

**内部動作:**
- `useOllamaModels` フックを内部で使用
- プロバイダー変更時、`ollama` なら自動的に `onBaseUrlChange(DEFAULT_OLLAMA_BASE_URL)` を呼ぶ
- Ollama 接続エラー時はアラートを表示し、TextInput にフォールバック
- Ollama 接続成功時はモデル一覧を Select で表示

**UI 構成:**
```
┌─────────────────────────────────────┐
│ Provider (Select)                   │
│ [Ollama ▼]                          │
├─────────────────────────────────────┤
│ Base URL (TextInput)                │
│ [http://localhost:11434]            │
├─────────────────────────────────────┤
│ ⚠ Ollamaサーバーに接続できません     │  ← エラー時のみ
├─────────────────────────────────────┤
│ Model (Select or TextInput)         │
└─────────────────────────────────────┘
```

### 共通コンポーネント（components/common/）

| コンポーネント | 説明 |
|---------------|------|
| `PagePlaceholder` | 未実装ページ用のプレースホルダー。タイトルを表示 |
| `PageContainer` | ページ共通のローディング、エラー、空状態を処理するコンテナ |
| `SplitLayout` | リストと詳細パネルの左右分割レイアウト |
| `OccurrenceList` | 用語の出現箇所リストを表示 |
| `AddTermModal` | 用語追加モーダル（除外用語/必須用語で共通） |
| `TermListTable` | 用語一覧テーブル（除外用語/必須用語で共通） |

#### AddTermModal

除外用語と必須用語の追加ダイアログを共通化したモーダルコンポーネント。

```typescript
interface AddTermModalProps {
  opened: boolean
  onClose: () => void
  onSubmit: (termText: string) => void
  title: string         // ダイアログタイトル（例: "除外用語を追加"）
  placeholder: string   // 入力欄のプレースホルダー
  isLoading: boolean    // 送信中のローディング状態
}
```

**機能:**
- テキスト入力 + 追加ボタン + キャンセルボタン
- 空文字のサブミットを防止（`trim()` チェック）
- サブミット後に入力欄を自動クリア
- クローズ時に入力状態をリセット

#### TermListTable

除外用語と必須用語の一覧表示を共通化したテーブルコンポーネント。

```typescript
interface TermListTableProps {
  terms: TermItem[] | undefined
  onDelete: (termId: number) => void
  isLoading: boolean
  isDeletePending: boolean
  showSourceColumn: boolean  // Source列の表示/非表示を制御
  deleteTooltip: string
  deleteAriaLabel: string
}
```

**機能:**
- 用語テキスト、ソースバッジ（自動/手動）、作成日時、削除ボタンを表示
- `showSourceColumn` で Source 列の表示/非表示を制御（除外用語: 表示、必須用語: 非表示）
- `LoadingOverlay` でローディング状態を表示
- 削除ボタンにツールチップとアクセシビリティ属性を設定

#### PageContainer

ページ共通のローディング、エラー、空状態をハンドリングするコンテナコンポーネント。
固定アクションバーとスクロール可能なコンテンツ領域を提供します。

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
  // カスタムレンダリング（オプション）
  renderLoading?: () => ReactNode
  renderEmpty?: () => ReactNode
  renderError?: (error: Error, onRetry?: () => void) => ReactNode
}
```

**レイアウト構造:**

CSS クラス（`styles/layout.css`）を使用してレイアウトを管理します：

```css
.page-layout { height: 100%; display: flex; flex-direction: column; }
.action-bar { flex-shrink: 0; border-bottom: 1px solid var(--mantine-color-gray-3); }
.scrollable-content { flex: 1; overflow-y: auto; min-height: 0; }
```

```
┌─────────────────────────────────────┐
│ ActionBar (.action-bar)             │ ← 固定
├─────────────────────────────────────┤
│                                     │
│ Content (.scrollable-content)       │ ← スクロール
│                                     │
└─────────────────────────────────────┘
```

**状態遷移:**
1. `isLoading: true` → `renderLoading` があればカスタム表示、なければデフォルトスピナー
2. `error` が存在 → `renderError` があればカスタム表示、なければデフォルトエラー
3. `isEmpty: true` → `renderEmpty` があればカスタム表示、なければデフォルト空状態
4. それ以外 → `children` を表示

**注意:** `isEmpty: true` の場合、`children` は表示されない。タブナビゲーションなど常に表示すべき要素が `children` に含まれる場合は、`isEmpty={false}` を渡し、各パネル内で空状態を処理する必要がある（TermsPage の実装を参照）。

**カスタムレンダリングの例（FilesPage）:**
```tsx
<PageContainer
  isLoading={isLoading}
  isEmpty={!files || files.length === 0}
  emptyMessage="No files"
  actionBar={<Title>Files</Title>}
  renderLoading={() => <Skeleton height={200} />}
  renderEmpty={() => (
    <Card>
      <Text>No files registered</Text>
      <Button>Add Files</Button>
    </Card>
  )}
>
  <Table>...</Table>
</PageContainer>
```

#### SplitLayout

リストと詳細パネルを左右に分割表示するレイアウトコンポーネント。`PageContainer` の `children` として使用します。

```typescript
interface SplitLayoutProps {
  list: ReactNode           // 左側: リスト部分
  detail: ReactNode | null  // 右側: 詳細パネル (nullで非表示)
}
```

**動作:**
- `detail` が `null` → リストが全幅を使用
- `detail` が存在 → リスト60%:詳細40% の分割表示
- 各パネルは独立してスクロール可能
- 768px以下では縦並びにフォールバック

**レイアウト構造:**

```
┌──────────────────┬───────────────────┐
│ list             │ detail            │
│ (.split-layout-  │ (.split-layout-   │
│  list, 60%)      │  detail, 40%)     │
│ 独立スクロール   │ 独立スクロール    │
└──────────────────┴───────────────────┘
```

**使用ページ:** TermsPage, ProvisionalPage, RefinedPage, IssuesPage

```tsx
<PageContainer actionBar={...}>
  <SplitLayout
    list={<Table>...</Table>}
    detail={selectedItem && <DetailPanel item={selectedItem} />}
  />
</PageContainer>
```

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
| `FileDetailResponse` | ファイル詳細（id, file_name, content_hash, content） |
| `TermResponse` | 抽出された用語（id, term_text, category, user_notes） |
| `TermOccurrence` | 用語の出現箇所（line_number, context） |
| `GlossaryTermResponse` | 用語集エントリ（term_name, definition, confidence, occurrences） |
| `IssueResponse` | 精査で見つかった問題（term_name, issue_type, description） |
| `LogMessage` | ログメッセージ（run_id, level, message, 進捗フィールド） |
| `RunResponse` | パイプライン実行状態（scope, status, progress, timestamps） |
| `SettingsResponse` | 設定（model_name, ollama_base_url, max_retries, timeout_seconds） |
| `PaginatedResponse<T>` | ページネーション付きレスポンス |
| `ErrorResponse` | エラーレスポンス |

### hooks/

TanStack Query を使用したカスタムフック。

#### 共通用語CRUDフック（useTermsCrud.ts）

除外用語と必須用語のデータフェッチ・ミューテーションを共通化したジェネリックフック群。

```typescript
interface UseTermsCrudOptions {
  /** API path segment, e.g. "excluded-terms" or "required-terms" */
  apiPath: string
  /** Query key prefix, e.g. "excludedTerms" or "requiredTerms" */
  queryKeyPrefix: string
}

// データフェッチ（ジェネリック型Tでレスポンス型を指定）
function useTermsList<T>(projectId: number | undefined, options: UseTermsCrudOptions)

// 用語追加ミューテーション
function useCreateTerm<T>(projectId: number, options: UseTermsCrudOptions)

// 用語削除ミューテーション
function useDeleteTerm(projectId: number, options: UseTermsCrudOptions)
```

**使用例（薄いラッパー）:**
```typescript
// useExcludedTerms.ts
const OPTIONS = { apiPath: 'excluded-terms', queryKeyPrefix: 'excludedTerms' } as const

export function useExcludedTerms(projectId: number | undefined) {
  const { keys: _keys, ...result } = useTermsList<ExcludedTermResponse>(projectId, OPTIONS)
  return result
}

export function useCreateExcludedTerm(projectId: number) {
  return useCreateTerm<ExcludedTermResponse>(projectId, OPTIONS)
}
```

**設計ポイント:**
- `apiPath` と `queryKeyPrefix` をパラメータ化し、APIパスとキャッシュキーを制御
- ミューテーション成功時に自分のリストと `termKeys.list` の両方を無効化（用語リストとの連携）
- `enabled: projectId !== undefined` で `projectId` 未確定時のフェッチを防止
- 個別フック（`useExcludedTerms.ts`, `useRequiredTerms.ts`）は薄いラッパーとして残す

#### データフェッチフック

| フック | 説明 |
|-------|------|
| `useTerms` | 用語一覧を取得 |
| `useExcludedTerms` | 除外用語一覧を取得（`useTermsCrud` ラッパー） |
| `useRequiredTerms` | 必須用語一覧を取得（`useTermsCrud` ラッパー） |
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
| `useCreateFile` / `useCreateFilesBulk` / `useDeleteFile` | ファイルの追加/一括追加/削除 |
| `useExtractTerms` | 用語抽出を実行 |
| `useCreateTerm` / `useUpdateTerm` / `useDeleteTerm` | 用語の追加/更新（user_notes含む）/削除 |
| `useCreateExcludedTerm` / `useDeleteExcludedTerm` | 除外用語の追加/削除（`useTermsCrud` ラッパー） |
| `useCreateRequiredTerm` / `useDeleteRequiredTerm` | 必須用語の追加/削除（`useTermsCrud` ラッパー） |
| `useUpdateProvisional` | 暫定用語集エントリを更新 |
| `useRegenerateProvisional` | 暫定用語集を再生成 |
| `useReviewIssues` | 問題精査を実行 |
| `useRegenerateRefined` | 最終用語集を再生成 |
| `useExportMarkdown` | Markdown 形式でエクスポート |

**ファイルミューテーションのキャッシュ無効化:**

ファイル操作（`useCreateFile`, `useCreateFilesBulk`, `useDeleteFile`）の `onSuccess` では以下のクエリを無効化：
- `fileKeys.list(projectId)` - ファイル一覧の更新
- `projectKeys.lists()` - プロジェクト一覧の `document_count` 更新
- `projectKeys.detail(projectId)` - プロジェクト詳細の `document_count` 更新

これにより、ファイル操作後にプロジェクト詳細画面のドキュメント数が正しく反映されます。

#### useLogStream

SSE（Server-Sent Events）を使用したログストリーミングフック。Zustand ストアと統合。

```typescript
interface UseLogStreamOptions {
  onComplete?: (projectId: number) => void  // ストリーム完了時のコールバック（projectIdはSSEコンテキストから）
}

interface UseLogStreamResult {
  logs: LogMessage[]      // ログメッセージ配列（Zustand ストアから取得）
  isConnected: boolean    // 接続状態
  error: Error | null     // エラー
  clearLogs: () => void   // ログクリア
}

export function useLogStream(
  projectId: number,
  runId: number | undefined,
  options?: UseLogStreamOptions
): UseLogStreamResult
```

**設計ポイント:**
- `getBaseUrl()` を使用して環境に応じた URL を生成
- Zustand ストア（`logStore`）にログを保存し、ページ遷移時も保持
- `projectId` または `runId` 変更時に自動でログをクリア（`setCurrentContext`を使用）
- プロジェクト間でのログ衝突を防止（同じrunIdでも異なるプロジェクトなら別扱い）
- メモリリーク防止のため最大1000件に制限
- クリーンアップ時に `EventSource.close()` を呼び出し
- `runId == null` チェックにより `runId = 0` を有効な値として正しく処理
- `onComplete` は `useRef` で保持し、stale closure 問題を回避

#### LogMessage 型

バックエンドから送信されるログメッセージ。進捗フィールドはオプショナル。

```typescript
interface LogMessage {
  run_id: number
  level: 'info' | 'warning' | 'error'
  message: string
  timestamp: string
  // 進捗情報（オプショナル）
  step?: string           // ステップ名（'provisional', 'refine'）
  progress_current?: number // 処理済み件数
  progress_total?: number   // 全件数
  current_term?: string     // 処理中の用語名
}
```

**進捗付きログメッセージの例:**
```json
{
  "run_id": 1,
  "level": "info",
  "message": "量子コンピュータ: 25%",
  "timestamp": "2026-01-30T12:00:00Z",
  "step": "provisional",
  "progress_current": 5,
  "progress_total": 20,
  "current_term": "量子コンピュータ"
}
```

## 状態管理（store/）

### Zustand

グローバル状態管理に Zustand を使用。軽量（~1KB）でシンプルな API を提供。

### logStore.ts

ログメッセージと進捗情報をグローバルに管理するストア。ページ遷移時もログを保持。

```typescript
interface LogProgress {
  step: string        // 現在のステップ名（'provisional', 'refine' など）
  current: number     // 処理済み件数
  total: number       // 全件数
  currentTerm: string // 処理中の用語名
}

interface LogStore {
  logs: LogMessage[]              // ログメッセージ配列（最大1000件）
  currentProjectId: number | null // 現在のプロジェクトID
  currentRunId: number | null     // 現在の実行ID
  latestProgress: LogProgress | null  // 最新の進捗情報
  addLog: (log: LogMessage) => void
  clearLogs: () => void
  setCurrentRunId: (runId: number | null) => void
  setCurrentContext: (projectId: number | null, runId: number | null) => void
}
```

**設計ポイント:**
- `addLog`: ログ追加時に進捗情報も自動更新。メモリ制限のため最大1000件に制限
- `setCurrentContext`: プロジェクトIDまたは実行IDが変更されたときにログと進捗情報をクリア。異なるプロジェクト間でのログ衝突を防止
- `setCurrentRunId`: 実行ID変更時にログと進捗情報をクリア（レガシーサポート）
- `latestProgress`: 最新の進捗情報を直接状態として保持（React の再レンダリング最適化）

**進捗情報の抽出:**
```typescript
function extractProgress(log: LogMessage): LogProgress | null {
  if (log.step !== undefined &&
      log.progress_current !== undefined &&
      log.progress_total !== undefined) {
    return {
      step: log.step,
      current: log.progress_current,
      total: log.progress_total,
      currentTerm: log.current_term ?? '',
    }
  }
  return null
}
```

**使用例:**
```typescript
// コンポーネントでの使用
const progress = useLogStore((state) => state.latestProgress)
const logs = useLogStore((state) => state.logs)

// アクションの呼び出し
useLogStore.getState().addLog(logMessage)
useLogStore.getState().setCurrentContext(projectId, runId)  // 推奨
useLogStore.getState().setCurrentRunId(newRunId)  // レガシー
```

## ユーティリティ（utils/）

### colors.ts

ステータスや重要度に応じた色定義とヘルパー関数。

```typescript
// 型定義はapi/types.tsからインポート
import type { RunStatus, IssueType } from '../api/types'

// IssueType は以下の値を持つ（バックエンドと同じ）:
// 'unclear' | 'contradiction' | 'missing_relation' | 'unnecessary'

// 色マッピング
export const statusColors: Record<RunStatus, string>
export const issueTypeColors: Record<IssueType, string>  // unclear: orange, contradiction: grape, missing_relation: cyan, unnecessary: gray
export const levelColors: Record<string, string>  // ログレベル用

// ヘルパー関数（型安全でデフォルト値付き）
export function getStatusColor(status: string): string
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
| `terms-workflow.test.tsx` | 74 | Terms/Provisional/Issues/Refined ページ、Run管理、LogPanel、カテゴリ編集、user_notes、タブ空状態表示 |
| `logStore.test.ts` | 20 | Zustand ログストアの状態管理、進捗追跡 |
| `LogPanel.test.tsx` | 5 | LogPanel の進捗表示UI |
| `useLogStream.test.ts` | 7 | useLogStream フックの runId=0 処理、onComplete コールバック、projectId引数 |

**合計**: 269 テスト

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

# 型チェック
pnpm typecheck
```

### Git Hooks

プロジェクトには Husky による pre-commit フックが設定されています。コミット前に `pnpm run typecheck` が自動実行され、型エラーがあるとコミットがブロックされます。

新規クローン後のセットアップ：
```bash
git config core.hooksPath .husky
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
