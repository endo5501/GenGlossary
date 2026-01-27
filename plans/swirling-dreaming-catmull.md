# 実装計画: GUI Frontend Terms/Provisional/Issues/Refined Views

チケット: `tickets/260124-164019-gui-frontend-terms-review.md`

## 概要

GUI フロントエンドの最終チケットとして、Terms/Provisional/Issues/Refined の各ビューと、グローバル実行制御（Run/Stop）、ログビューアを実装します。

## ファイル構成

### 新規作成ファイル

```
frontend/src/
├── api/hooks/
│   ├── useTerms.ts           # Terms API hooks
│   ├── useProvisional.ts     # Provisional API hooks
│   ├── useIssues.ts          # Issues API hooks
│   ├── useRefined.ts         # Refined API hooks
│   ├── useRuns.ts            # Runs API hooks
│   └── useLogStream.ts       # SSE ログストリーム hook
├── pages/
│   ├── TermsPage.tsx
│   ├── ProvisionalPage.tsx
│   ├── IssuesPage.tsx
│   └── RefinedPage.tsx
└── __tests__/
    └── terms-workflow.test.tsx
```

### 修正ファイル

| ファイル | 修正内容 |
|---------|---------|
| `frontend/src/api/types.ts` | TermOccurrence に document_path 追加、LogMessage 型追加 |
| `frontend/src/api/hooks/index.ts` | 新規 hooks の export |
| `frontend/src/routes/index.tsx` | 新規ルート追加 |
| `frontend/src/components/layout/GlobalTopBar.tsx` | useRuns で API 接続 |
| `frontend/src/components/layout/LogPanel.tsx` | SSE ストリーム対応 |
| `frontend/src/components/layout/AppShell.tsx` | GlobalTopBar に projectId 伝搬 |
| `frontend/src/mocks/handlers.ts` | 新規 API ハンドラー追加 |
| `frontend/src/pages/index.ts` | 新規ページ export |

## 実装順序 (TDD)

### Phase 1: Red - テスト作成

1. **`frontend/src/__tests__/terms-workflow.test.tsx` 作成**
   - TermsPage テスト（テーブル表示、詳細パネル、アクション）
   - ProvisionalPage テスト（テーブル、エディタ、regenerate）
   - IssuesPage テスト（フィルタ、詳細パネル）
   - RefinedPage テスト（リスト、export）
   - GlobalTopBar API 接続テスト
   - LogPanel SSE テスト

2. **テスト失敗確認**

### Phase 2: Green - 実装

#### Step 1: 型定義とモックデータ

**`frontend/src/api/types.ts` 修正**
```typescript
// TermOccurrence に document_path 追加
export interface TermOccurrence {
  document_path: string  // 追加
  line_number: number
  context: string
}

// LogMessage 型追加
export interface LogMessage {
  run_id: number
  level: 'info' | 'warning' | 'error'
  message: string
  complete?: boolean
}
```

**`frontend/src/mocks/handlers.ts` 追加**
- GET/POST/PATCH/DELETE `/api/projects/:pid/terms`
- GET/PATCH/POST `/api/projects/:pid/provisional`
- GET `/api/projects/:pid/issues`
- GET `/api/projects/:pid/refined`
- Runs API handlers

#### Step 2: API hooks 実装

**`useTerms.ts`**
```typescript
export const termKeys = {
  all: ['terms'] as const,
  list: (projectId: number) => [...termKeys.all, 'list', projectId] as const,
  detail: (projectId: number, termId: number) => [...termKeys.all, 'detail', projectId, termId] as const,
}

export function useTerms(projectId: number | undefined)
export function useTerm(projectId: number | undefined, termId: number | undefined)
export function useCreateTerm(projectId: number)
export function useUpdateTerm(projectId: number)
export function useDeleteTerm(projectId: number)
```

**`useProvisional.ts`**
```typescript
export function useProvisional(projectId: number | undefined)
export function useProvisionalEntry(projectId: number | undefined, entryId: number | undefined)
export function useUpdateProvisional(projectId: number)
export function useRegenerateProvisional(projectId: number)
```

**`useIssues.ts`**
```typescript
export function useIssues(projectId: number | undefined, issueType?: string)
export function useIssue(projectId: number | undefined, issueId: number | undefined)
```

**`useRefined.ts`**
```typescript
export function useRefined(projectId: number | undefined)
export function useRefinedEntry(projectId: number | undefined, termId: number | undefined)
export function useExportMarkdown(projectId: number)
```

**`useRuns.ts`**
```typescript
export function useCurrentRun(projectId: number | undefined)
export function useStartRun(projectId: number)
export function useCancelRun(projectId: number)
```

**`useLogStream.ts`**
```typescript
export function useLogStream(projectId: number, runId: number | undefined): {
  logs: LogMessage[]
  isConnected: boolean
  error: Error | null
}
```

#### Step 3: ページコンポーネント実装

**`TermsPage.tsx`**
- 上部: アクションバー（再抽出、手動追加ボタン）
- 中央: テーブル（term_text / category / occurrences count）
- 下部: 詳細パネル（occurrences リスト、exclude/edit アクション）
- 実行中はアクションボタン無効化

**`ProvisionalPage.tsx`**
- 上部: アクションバー（暫定用語集再生成ボタン）
- 中央: テーブル（term_name / definition / confidence）
- 下部: 詳細エディタ（definition textarea、confidence slider、regenerate ボタン）

**`IssuesPage.tsx`**
- 上部: アクションバー（精査再実行ボタン）+ フィルタセレクト
- 中央: リスト（issue_type バッジ付き）
- 下部: 詳細パネル（description 表示）

**`RefinedPage.tsx`**
- 上部: アクションバー（最終用語集再生成、Markdown エクスポート）
- 中央: リスト（term_name / definition）
- 下部: 詳細パネル（occurrences リスト）

#### Step 4: ルーティング修正

**`frontend/src/routes/index.tsx`**
```typescript
const projectTermsRoute = createRoute({
  path: '/projects/$projectId/terms',
  component: TermsPage,
})
// 同様に provisional, issues, refined
```

**`LeftNavRail.tsx`** - projectScoped を全て true に

#### Step 5: GlobalTopBar と LogPanel 修正

**`GlobalTopBar.tsx`**
- props から API 呼び出しに変更
- `useCurrentRun(projectId)` でステータス取得
- `useStartRun(projectId)` で Run ボタン
- `useCancelRun(projectId)` で Stop ボタン

**`AppShell.tsx`**
- URL から projectId を抽出
- GlobalTopBar に projectId を渡す

**`LogPanel.tsx`**
- `useLogStream(projectId, runId)` で SSE 接続
- ログメッセージをリアルタイム表示
- 自動スクロール

### Phase 3: テスト通過確認とリファクタリング

1. `npm run test` で全テスト通過確認
2. `npm run build` でビルド成功確認
3. code-simplifier agent でコードレビュー
4. codex MCP でコードレビュー

### Phase 4: ドキュメント更新

1. `docs/architecture/*.md` 更新
   - ログ/状態連携の記述追加

### Phase 5: 最終確認

1. `pyright` で静的解析（バックエンド）
2. `uv run pytest` で全テスト通過

## 技術的考慮事項

### SSE 接続管理

```typescript
// useLogStream.ts
useEffect(() => {
  if (!runId) return
  const url = `${BASE_URL}/api/projects/${projectId}/runs/${runId}/logs`
  const eventSource = new EventSource(url)

  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data)
    setLogs(prev => [...prev, data])
  }

  eventSource.addEventListener('complete', () => {
    eventSource.close()
  })

  return () => eventSource.close()
}, [projectId, runId])
```

### 実行中のアクション無効化

```typescript
const { data: currentRun } = useCurrentRun(projectId)
const isRunning = currentRun?.status === 'running'
// ボタンに disabled={isRunning}
```

### Markdown エクスポート

```typescript
const blob = new Blob([markdown], { type: 'text/markdown' })
const url = URL.createObjectURL(blob)
// ダウンロードリンク生成
```

## 検証方法

1. **ユニットテスト**: `npm run test` で全テスト通過
2. **ビルド**: `npm run build` で成功
3. **E2E 手動テスト**:
   - プロジェクト作成 → Files でファイル追加 → Run 実行
   - Terms/Provisional/Issues/Refined の各ページで表示確認
   - LogPanel でログストリーム確認
   - Markdown エクスポート確認
4. **バックエンドテスト**: `uv run pytest` で全テスト通過
5. **静的解析**: `pyright` で警告なし
