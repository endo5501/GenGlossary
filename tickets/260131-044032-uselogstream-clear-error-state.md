---
priority: 3
tags: [frontend, bug]
description: "useLogStream: Clear error state when runId becomes undefined"
created_at: "2026-01-31T04:40:32Z"
started_at: 2026-02-01T07:34:18Z # Do not modify manually
closed_at: 2026-02-01T07:46:13Z # Do not modify manually
---

# useLogStream: Clear error state when runId becomes undefined

## 概要

`useLogStream` フックで、`runId` が `null/undefined` になった際に `error` 状態がクリアされない問題。

## 問題点

- 場所: `frontend/src/api/hooks/useLogStream.ts:50-53`
- `runId` が無効値になっても、前回の SSE エラーが `error` state に残る
- UIが古いエラーを表示し続ける可能性がある

## 提案される修正

```typescript
useEffect(() => {
  if (runId == null) {
    setIsConnected(false)
    setError(null)  // Clear error when no run is active
    return
  }
  // ...
}, [projectId, runId, addLog])
```

## Tasks

- [x] TDDでテストを先に作成
- [x] 修正を実装
- [x] Commit
- [x] Run tests (`pnpm test`) before reviewing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Run tests (`pnpm test`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing

## Notes

- codex MCP コードレビューで発見 (260130-frontend-small-fixes チケット作業中)
- 緊急性は低い（潜在的なUIの問題）
- code-simplifier のリファクタリング提案は別チケット化: `260201-uselogstream-refactoring.md`
