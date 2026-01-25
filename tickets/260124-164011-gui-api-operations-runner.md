---
priority: 5
tags: [api, jobs, cli]
description: "Expose glossary pipeline operations over HTTP and add a background run/queue subsystem with log streaming."
created_at: "2026-01-24T16:40:11Z"
started_at: 2026-01-25T13:45:02Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# Ticket Overview

Bridge the existing CLI pipeline (extract → provisional → issues → refined) into API-accessible operations. Introduce a lightweight run manager to dispatch tasks asynchronously, persist run status, and stream logs so the GUI can start/stop/monitor executions per project.

Reference: `plan-gui.md` 「グローバル操作バー」「ログビュー」「各タブの再実行ボタン」実現のサーバ側。


## Tasks

### TDD Phase (Completed ✅)
- [x] **Red**: 先にテスト追加（`tests/db/test_runs_repository.py`, `tests/runs/test_manager.py`）— CRUD, start/stop, status遷移、プロジェクト別隔離
- [x] テストが失敗することを確認（Red完了）— ModuleNotFoundError確認済み
- [x] **Green**: 実装完了とコアテスト通過 (33 tests passed)

### Implementation (Completed ✅)
- [x] Add run/queue abstraction (threaded background tasks) with cancellation hooks and status tracking — RunManager + threading.Event実装
- [x] Create API endpoints to trigger Full/From-Terms/etc. runs for a project, and to stop a running job — `/api/projects/{id}/runs` エンドポイント実装
- [x] Implement log capture/streaming (SSE) plus run history retrieval — Queue + SSE準備完了
- [x] Persist run records (status, started_at, finished_at, triggered_by, scope) in DB — runs table実装 (schema v3)

### Remaining Tasks
- [x] Reuse existing CLI commands internally instead of duplicating pipeline logic — ✅ PipelineExecutorに実際のパイプライン統合完了
- [x] Fix API integration tests — ✅ SQLite threading問題を解決し、API統合テスト10件追加
- [x] Update docs/architecture.md — ✅ Run管理セクション追記完了
- [ ] Code simplification review using code-simplifier agent
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions) — ✅ 0 errors
- [x] Run full test suite (`uv run pytest`) before closing — ✅ 631 tests passed
- [ ] Get developer approval before closing


## Implementation Summary

### Completed Components

**Database Layer (schema v3)**
- `runs` table: id, scope, status, started_at, finished_at, triggered_by, error_message, progress_current, progress_total, current_step, created_at
- `runs_repository.py`: create_run, get_run, get_active_run, list_runs, update_run_status, update_run_progress, cancel_run

**Run Management**
- `RunManager`: スレッドベースのバックグラウンド実行管理
- プロジェクトごとに1つのアクティブRunのみ許可
- threading.Eventによるキャンセルサポート
- Queue経由のログストリーミング

**API Layer**
- POST `/api/projects/{id}/runs` - Run開始
- DELETE `/api/projects/{id}/runs/{run_id}` - Runキャンセル
- GET `/api/projects/{id}/runs` - Run履歴一覧
- GET `/api/projects/{id}/runs/current` - アクティブRun取得
- GET `/api/projects/{id}/runs/{run_id}` - Run詳細
- GET `/api/projects/{id}/runs/{run_id}/logs` - SSEログストリーミング

**Test Coverage**
- Repository: 20 tests ✅
- RunManager: 13 tests ✅
- PipelineExecutor: 5 tests ✅
- API Integration: 10 tests ✅
- Total: 48 new Run-related tests
- Full suite: 631 tests passing ✅

### Completed Implementation ✅

1. **PipelineExecutor**: ✅ 実際のパイプライン（DocumentLoader, TermExtractor, GlossaryGenerator, GlossaryReviewer, GlossaryRefiner）統合完了
2. **SQLite Threading**: ✅ db_path方式に変更し、各スレッドが独自の接続を作成する方式で解決
3. **API Tests**: ✅ API統合テスト10件を実装、全テスト成功
4. **Documentation**: ✅ `docs/architecture.md`にRun管理セクション追記完了
5. **Static Analysis**: ✅ pyright 0 errors
6. **Full Test Suite**: ✅ 631 tests passing

### Remaining for Closure

1. Optional: code-simplifier agentによるコードレビュー
2. Developer approval

## Notes

Prefer SSE for simplicity; leave room to swap transport. Ensure runs respect project isolation and do not lock the main event loop. Provide graceful shutdown handling.

**Threading Architecture**: 各RunManagerインスタンスはdb_pathを保持し、バックグラウンドスレッド内で独自の接続を作成。これにより、APIリクエストとバックグラウンド処理でSQLite接続を共有せず、スレッドセーフな実行を実現。
