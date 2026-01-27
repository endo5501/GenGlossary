# Codex レビュー指摘事項の修正計画

チケット: `tickets/260124-164019-gui-frontend-terms-review.md`

## 概要

codex MCP によるコードレビューで指摘された問題を修正します。

## 修正対象ファイル

| ファイル | 修正内容 |
|---------|---------|
| `frontend/src/api/client.ts` | `getBaseUrl()` を export |
| `frontend/src/api/hooks/useLogStream.ts` | BASE_URL を getBaseUrl() に変更、runId 変更時にログクリア |
| `frontend/src/api/hooks/useRefined.ts` | ハードコードされた URL を getBaseUrl() に変更 |
| `frontend/src/utils/colors.ts` | 型安全性の向上 |
| `frontend/src/components/common/OccurrenceList.tsx` | 安定したキーを使用 |
| `frontend/src/components/layout/LogPanel.tsx` | 安定したキーを使用 |
| `frontend/src/components/common/PageContainer.tsx` | エラー状態の表示を追加 |
| `frontend/src/pages/TermsPage.tsx` | ID ベースの選択、キーボードアクセシビリティ |
| `frontend/src/pages/ProvisionalPage.tsx` | ID ベースの選択、キーボードアクセシビリティ |
| `frontend/src/pages/IssuesPage.tsx` | ID ベースの選択、キーボードアクセシビリティ |
| `frontend/src/pages/RefinedPage.tsx` | ID ベースの選択、キーボードアクセシビリティ |

## 修正詳細

### 1. 高優先度: BASE_URL のハードコード修正

**`frontend/src/api/hooks/useLogStream.ts`**
```typescript
// Before
const BASE_URL = 'http://localhost:8000'

// After
import { getBaseUrl } from '../client'
// getBaseUrl() を使用
```

**`frontend/src/api/hooks/useRefined.ts`**
```typescript
// Before (exportMarkdown 関数内)
const response = await fetch(`http://localhost:8000/api/projects/${projectId}/refined/export`)

// After
const response = await fetch(`${getBaseUrl()}/api/projects/${projectId}/refined/export`)
```

### 2. 高優先度: ログストリームのメモリリーク修正

**`frontend/src/api/hooks/useLogStream.ts`**
```typescript
// runId 変更時にログをクリア
useEffect(() => {
  setLogs([])  // runId が変わったらログをリセット
}, [runId])

// ログの最大件数を制限（オプション）
const MAX_LOGS = 1000
setLogs((prev) => {
  const newLogs = [...prev, log]
  return newLogs.length > MAX_LOGS ? newLogs.slice(-MAX_LOGS) : newLogs
})
```

### 3. 中優先度: エラー状態の表示

**`frontend/src/components/common/PageContainer.tsx`**
```typescript
interface PageContainerProps {
  // 既存のプロパティ
  isLoading: boolean
  isEmpty: boolean
  emptyMessage: string
  actionBar: ReactNode
  children: ReactNode
  // 追加
  error?: Error | null
  onRetry?: () => void
}

// エラー時の表示を追加
if (error) {
  return (
    <Stack>
      {actionBar}
      <Center h={200}>
        <Stack align="center">
          <Text c="red">Error: {error.message}</Text>
          {onRetry && <Button onClick={onRetry}>Retry</Button>}
        </Stack>
      </Center>
    </Stack>
  )
}
```

### 4. 中優先度: ID ベースの選択

**各ページコンポーネント (TermsPage, ProvisionalPage, IssuesPage, RefinedPage)**
```typescript
// Before
const [selectedTerm, setSelectedTerm] = useState<TermDetailResponse | null>(null)

// After
const [selectedId, setSelectedId] = useState<number | null>(null)
const selectedTerm = terms?.find(t => t.id === selectedId) ?? null
```

### 5. 中優先度: キーボードアクセシビリティ

**各ページのテーブル行**
```typescript
// Before
<Table.Tr
  onClick={() => setSelectedId(term.id)}
  style={{ cursor: 'pointer' }}
>

// After
<Table.Tr
  onClick={() => setSelectedId(term.id)}
  onKeyDown={(e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      setSelectedId(term.id)
    }
  }}
  tabIndex={0}
  role="button"
  aria-selected={selectedId === term.id}
  style={{ cursor: 'pointer' }}
>
```

### 6. 低優先度: 安定したキー

**`frontend/src/components/common/OccurrenceList.tsx`**
```typescript
// Before
{occurrences.map((occ, idx) => (
  <Paper key={idx} ...>

// After
{occurrences.map((occ) => (
  <Paper key={`${occ.document_path}:${occ.line_number}`} ...>
```

**`frontend/src/components/layout/LogPanel.tsx`**
```typescript
// Before
{logs.map((log, idx) => (
  <Text key={idx} ...>

// After
{logs.map((log, idx) => (
  <Text key={`${log.run_id}-${idx}`} ...>
```

### 7. 低優先度: 型安全性の向上

**`frontend/src/utils/colors.ts`**
```typescript
// Before
export const statusColors: Record<string, string> = { ... }

// After
export type RunStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
export const statusColors: Record<RunStatus, string> = { ... }

// デフォルト値付きの取得関数
export function getStatusColor(status: string): string {
  return statusColors[status as RunStatus] ?? 'var(--mantine-color-gray-5)'
}
```

## 実装順序

1. `client.ts` - `getBaseUrl()` が既に export されていることを確認
2. `useLogStream.ts` - BASE_URL 修正 + ログクリア
3. `useRefined.ts` - BASE_URL 修正
4. `utils/colors.ts` - 型安全性向上
5. `PageContainer.tsx` - エラー状態追加
6. `OccurrenceList.tsx` - 安定したキー
7. `LogPanel.tsx` - 安定したキー
8. 各ページ - ID ベース選択 + アクセシビリティ

## 検証方法

1. **テスト実行**: `cd frontend && npm test`
2. **ビルド確認**: `cd frontend && npm run build`
3. **手動確認**:
   - 各ページでキーボード操作（Tab + Enter）が動作すること
   - エラー時にエラーメッセージが表示されること
   - ログがrun切り替え時にクリアされること
