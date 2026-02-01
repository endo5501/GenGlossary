---
priority: 2
tags: [frontend, refactoring]
description: "useLogStream: Refactor for improved readability and maintainability"
created_at: "2026-02-01T16:40:00Z"
started_at: 2026-02-01T07:46:55Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# useLogStream: Refactor for improved readability and maintainability

## 概要

`useLogStream` フックのコードをリファクタリングし、可読性と保守性を向上させる。

## 対象ファイル

- `frontend/src/api/hooks/useLogStream.ts`

## 提案される改善

### 1. 共通の切断ロジックを関数に抽出

**現状**: `eventSource.close()` と `setIsConnected(false)` が3箇所に重複

```typescript
// 提案
const disconnect = () => {
  eventSource.close()
  setIsConnected(false)
}
```

### 2. イベントハンドラーを名前付き関数に統一

**現状**: インラインの無名関数と `addEventListener` が混在

```typescript
// 提案
const handleOpen = () => {
  setIsConnected(true)
  setError(null)
}

const handleMessage = (event: MessageEvent) => {
  const log = parseLogMessage(event)
  if (log) addLog(log)
}

const handleComplete = () => {
  disconnect()
  onCompleteRef.current?.()
}

const handleError = () => {
  setError(new Error('SSE connection error'))
  disconnect()
}
```

### 3. cleanup関数の簡潔化

**現状**: 無名関数で個別に記述
**提案**: `return disconnect` で1行に

## 注意事項

- Error オブジェクトの定数化は非推奨（React が state 更新をスキップする可能性あり - codex MCP 指摘）

## Tasks

- [x] TDDでテストを先に作成（既存テストが網羅的か確認）
- [x] リファクタリング実装
- [x] Commit
- [x] Run tests (\`pnpm test\`) before reviewing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Run tests (\`pnpm test\`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## Notes

- code-simplifier エージェントで発見 (260131-044032-uselogstream-clear-error-state チケット作業中)
- 機能変更なし、リファクタリングのみ
- codex MCP レビューで removeEventListener 欠落を発見 → 別チケット作成: 260201-075029-uselogstream-event-listener-cleanup
