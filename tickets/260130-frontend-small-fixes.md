---
priority: 7
tags: [refactoring, code-quality, frontend]
description: "Frontend: Small bug fixes in useLogStream"
created_at: "2026-01-30T09:45:00Z"
started_at: null
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

- [ ] テストを追加・更新
- [ ] 実装
- [ ] Run tests (`pnpm test`) and pass all tests
- [ ] Get developer approval before closing

## Notes

- 現状で顕在化していないバグだが、潜在的な問題
- 緊急性は低い
