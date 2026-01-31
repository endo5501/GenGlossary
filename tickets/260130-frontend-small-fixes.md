---
priority: 2
tags: [refactoring, code-quality, frontend]
description: "Frontend: Small bug fixes in useLogStream"
created_at: "2026-01-30T09:45:00Z"
started_at: 2026-01-31T04:34:33Z
closed_at: null
---

# Frontend: Small bug fixes in useLogStream

## 概要

`useLogStream.ts` の小規模なバグ修正。

## 対応項目

### 1. `runId = 0` の falsy 問題
- 場所: `useLogStream.ts:46`
- `if (!runId)` で 0 が "no run" 扱いになる
- 対策: `runId === undefined` または `runId == null` に変更

### 2. `onComplete` の stale closure
- 場所: `useLogStream.ts:67`
- `onComplete` が依存配列に含まれていない
- 対策: 依存配列に `onComplete` を追加

## Tasks

- [x] テストを追加・更新
- [x] `runId = 0` の falsy 問題修正
- [x] `onComplete` の stale closure実装
- [x] Run tests (`pnpm test`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Update docs/architecture/*.md
- [x] Run tests (`pnpm test`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing


## Notes

- 現状で顕在化していないバグだが、潜在的な問題
- 緊急性は低い
- code-simplifier: 不要な useCallback を削除
- codex MCP: stale error state 問題を発見 → 別チケット作成 (260131-044032-uselogstream-clear-error-state)
