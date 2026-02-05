---
priority: 2
tags: [bug, frontend, edge-case]
description: "handleRunCompleteがSSEコンテキストからprojectIdを受け取るべき"
created_at: "2026-02-03T22:27:52Z"
started_at: 2026-02-05T14:46:07Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# handleRunComplete should receive projectId from SSE context

## 概要

`AppShell.tsx`の`handleRunComplete`コールバックは、現在のロケーションから`projectId`を取得しているが、SSE完了イベントが発火した時点で、ユーザーが別のプロジェクトに移動している可能性がある。この場合、間違ったプロジェクトのキャッシュが無効化される。

## 問題の詳細

1. **タイミングの問題**: SSEの`complete`イベントがEventSourceを閉じる直前に発火した場合、クリーンアップ関数が呼ばれる前に`handleComplete`が実行される可能性がある
2. **ナビゲーション中のinvalidation**: ユーザーがRunの完了を待たずに別のプロジェクトに移動した場合、新しいプロジェクトのキャッシュが無効化される
3. **非プロジェクトルートでのinvalidation漏れ**: SSEの`complete`が非プロジェクトルートで発火した場合、`projectId`が`undefined`となりinvalidationがスキップされる

## 修正方針

`onRunComplete`コールバックに`projectId`（およびオプションで`runId`）を引数として渡し、SSEコンテキストに基づいてキャッシュを無効化する。

```typescript
// LogPanelProps
interface LogPanelProps {
  projectId?: number
  runId?: number
  onRunComplete?: (projectId: number) => void  // projectIdを引数として追加
}

// AppShell.tsx
const handleRunComplete = useCallback((completedProjectId: number) => {
  queryClient.invalidateQueries({ queryKey: runKeys.current(completedProjectId) })
  // ... 他のinvalidation
}, [queryClient])
```

## Tasks

- [x] `useLogStream`の`onComplete`コールバックに`projectId`を渡す
- [x] `LogPanel`の`onRunComplete`コールバックの型を更新
- [x] `AppShell`の`handleRunComplete`を更新して引数から`projectId`を受け取る
- [x] テストの追加
- [x] Commit
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Update docs/architecture/*.md
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing


## Notes

- このバグはエッジケースであり、通常のユーザー操作では発生しにくい
- codex MCPのコードレビューで指摘された問題
- 関連コミット: ef06546 (Fix auto-refresh of data lists after run completion)
