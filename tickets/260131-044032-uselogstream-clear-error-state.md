---
priority: 4
tags: [frontend, bug]
description: "useLogStream: Clear error state when runId becomes undefined"
created_at: "2026-01-31T04:40:32Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
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

- [ ] TDDでテストを先に作成
- [ ] 修正を実装
- [ ] Commit
- [ ] Run tests (`pnpm test`) before reviewing and pass all tests (No exceptions)
- [ ] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Run tests (`pnpm test`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## Notes

- codex MCP コードレビューで発見 (260130-frontend-small-fixes チケット作業中)
- 緊急性は低い（潜在的なUIの問題）
