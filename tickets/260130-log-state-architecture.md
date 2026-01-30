---
priority: 8
tags: [refactoring, architecture, frontend, backend]
description: "Log state architecture improvement"
created_at: "2026-01-30T09:45:00Z"
started_at: null
closed_at: null
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

- `frontend/src/stores/logStore.ts`
- `frontend/src/hooks/useLogStream.ts`
- `src/genglossary/runs/executor.py`
- `src/genglossary/api/schemas/run_schemas.py`

## Tasks

- [ ] 設計検討
- [ ] テストを追加・更新
- [ ] 実装
- [ ] Run static analysis and pass all tests
- [ ] Run tests (`uv run pytest` & `pnpm test`) and pass all tests
- [ ] Get developer approval before closing

## Notes

- 設計変更を伴うため、慎重に進める
- 複数プロジェクトを同時に開く場合のみ問題が顕在化
