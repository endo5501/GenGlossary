---
priority: 5
tags: [api, jobs, cli]
description: "Expose glossary pipeline operations over HTTP and add a background run/queue subsystem with log streaming."
created_at: "2026-01-24T16:40:11Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# Ticket Overview

Bridge the existing CLI pipeline (extract → provisional → issues → refined) into API-accessible operations. Introduce a lightweight run manager to dispatch tasks asynchronously, persist run status, and stream logs so the GUI can start/stop/monitor executions per project.

Reference: `plan-gui.md` 「グローバル操作バー」「ログビュー」「各タブの再実行ボタン」実現のサーバ側。


## Tasks

- [ ] **Red**: 先にテスト追加（`tests/api/test_runs.py`, `tests/db/test_runs_repository.py`）— start/stop, status遷移、SSE/WSストリーム、プロジェクト別隔離、CLIパイプライン呼び出しのモック検証
- [ ] テストが失敗することを確認（Red完了）
- [ ] Add run/queue abstraction (threaded or async background tasks) with cancellation hooks and status tracking — フロントの停止ボタンに対応
- [ ] Create API endpoints to trigger Full/From-Terms/etc. runs for a project, and to stop a running job — plan-guiの「実行範囲ドロップダウン」に対応
- [ ] Implement log capture/streaming (SSE or WebSocket) plus run history retrieval — 「ログビュー」「進行状況バッジ」に供給
- [ ] Reuse existing CLI commands internally instead of duplicating pipeline logic; ensure correct working directory per project
- [ ] Persist run records (status, started_at, finished_at, triggered_by, scope) in DB（`docs/architecture.md` のRun管理セクション追記）
- [ ] **Green**: 追加テストを含めpytest通過を確認
- [ ] Code simplification review using code-simplifier agent
- [ ] Update docs/architecture.md
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing


## Notes

Prefer SSE for simplicity; leave room to swap transport. Ensure runs respect project isolation and do not lock the main event loop. Provide graceful shutdown handling.
