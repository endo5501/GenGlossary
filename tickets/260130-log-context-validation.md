---
priority: 2
tags: [enhancement, frontend, log-system]
description: "LogStore: Add context validation in addLog"
created_at: "2026-01-30T10:20:00Z"
started_at: 2026-01-30T11:14:38Z
closed_at: null
---

# LogStore: Add context validation in addLog

## 概要

`addLog`がログメッセージのコンテキスト（projectId, runId）を検証していないため、
古いSSEストリームからのメッセージが誤ったコンテキストに追加される可能性がある。

## 問題の詳細

codex MCPレビューで指摘:
> Medium: `addLog` does not validate `currentProjectId/currentRunId`, so stale SSE
> messages (e.g., a previous stream still emitting after a context switch) or
> multiple mounted `useLogStream` hooks will still append logs and update
> `latestProgress` from the wrong context.

## 対策案

1. `addLog`でログのrun_idと`currentRunId`を比較し、一致しない場合は無視
2. または、EventSource切断時のクリーンアップを確実に行う

## 影響範囲

- `frontend/src/store/logStore.ts`
- `frontend/src/api/hooks/useLogStream.ts`

## Tasks

- [x] 設計検討
- [x] テスト追加
- [x] 実装
- [x] Run tests before closing

## 実装サマリー

### 対策内容
対策案1を採用: `addLog`でログの`run_id`と`currentRunId`を比較し、一致しない場合は無視

### 変更ファイル
- `frontend/src/store/logStore.ts`: `addLog`にコンテキストバリデーション追加
- `frontend/src/__tests__/logStore.test.ts`: バリデーションのテスト追加、既存テストを修正

### テスト結果
- Frontend: 162 tests passed
- Backend: 730 tests passed

## Notes

- 260130-log-state-architecture チケットのレビューで発見
- 複数のuseLogStreamフックがマウントされた場合の動作も考慮が必要
