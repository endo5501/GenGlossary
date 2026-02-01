---
priority: 5
tags: [frontend, bugfix]
description: "useLogStream: Add removeEventListener for complete event to prevent memory leaks"
created_at: "2026-02-01T07:50:29Z"
started_at: 2026-02-01T11:18:02Z # Do not modify manually
closed_at: 2026-02-01T11:21:56Z # Do not modify manually
---

# useLogStream: Add removeEventListener for complete event

## 概要

`useLogStream` フックで 'complete' イベントリスナーのクリーンアップが欠落している。
`EventSource.close()` は内部でリスナーを解放するが、ポリフィルや特殊なケースでリークが発生する可能性がある。

## 対象ファイル

- `frontend/src/api/hooks/useLogStream.ts`

## 問題

現在のcleanup関数：
```typescript
return disconnect
```

`removeEventListener` が呼ばれていないため、エッジケースでメモリリークの可能性がある。

## 修正案

```typescript
return () => {
  eventSource.removeEventListener('complete', handleComplete)
  disconnect()
}
```

## Tasks

- [x] TDDでテストを先に作成
- [x] 修正実装
- [x] Commit
- [x] Run tests (`pnpm test`) before reviewing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Run tests (`pnpm test`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing

## Notes

- codex MCP レビューで発見 (260201-uselogstream-refactoring チケット作業中)
- 将来的にエラーハンドリング強化も検討（別チケット）
