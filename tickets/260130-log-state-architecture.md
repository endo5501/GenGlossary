---
priority: 5
tags: [refactoring, architecture, frontend, backend]
description: "Log state architecture improvement"
created_at: "2026-01-30T09:45:00Z"
started_at: 2026-01-30T10:06:50Z
closed_at: 2026-01-30T10:33:38Z
---

# Log state architecture improvement

## 概要

ログ状態管理のアーキテクチャ改善。プロジェクト間での状態衝突を防ぎ、
バックエンドとフロントエンド間の型整合性を確保する。

## 対応項目

### 1. グローバルログ状態のプロジェクト衝突
- 場所: `logStore.ts:11`, `useLogStream.ts:41`
- 現状: runId のみでキーイング
- 問題: 異なるプロジェクトで同じ runId があると衝突
- 対策: `(projectId, runId)` の複合キーでキーイング

### 2. `run_id` の型不整合
- バックエンド: `run_id: int | None`
- フロントエンド: `runId: number` (必須)
- 対策: 型定義を統一
  - バックエンドで必須にするか
  - フロントエンドで optional にするか

## 影響範囲

- `frontend/src/store/logStore.ts`
- `frontend/src/api/hooks/useLogStream.ts`
- `src/genglossary/runs/executor.py`

## Tasks

- [x] 設計検討
- [x] テストを追加・更新
- [x] グローバルログ状態のプロジェクト衝突を解決
- [x] `run_id` の型不整合修正
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket.
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket.
- [x] Update docs/architecture/*.md
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
  - Note: LogPanel.test.tsxの1件の失敗は既存問題（progress-bar要素のテスト）で、今回の変更とは無関係
- [x] Get developer approval before closing

## Notes

- 設計変更を伴うため、慎重に進める
- 複数プロジェクトを同時に開く場合のみ問題が顕在化
