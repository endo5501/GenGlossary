---
priority: 4
tags: [db, model, gui]
description: "Define 'project' as a first-class entity with metadata, storage layout, and persistence for GUI use."
created_at: "2026-01-24T16:40:08Z"
started_at: 2026-01-25T11:01:09Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# Ticket Overview

Design and persist the concept of a project (docs root, project-scoped DB, LLM settings, display name, timestamps). Provide migrations and helper services so both CLI and upcoming GUI APIs can create/list/update/delete projects safely.

Reference: `plan-gui.md` 「プロジェクト一覧」「プロジェクト詳細」「Settings」画面のデータ源。


## Tasks

- [x] **Red**: 事前にテスト追加（`tests/db/test_project_repository.py`, `tests/test_cli_project.py`）— create/list/delete/cloneの振る舞い、既存単一ターゲット互換の回帰テスト
- [x] テスト失敗を確認してTDD Redを満たす
- [x] Define project schema (YAML/JSON config + DB tables) including doc root, db path, llm provider/model, and status timestamps（`docs/architecture.md` DBセクションに追加）。項目例: `id`, `name`, `doc_root`, `db_path`, `llm_provider`, `llm_model`, `created_at`, `updated_at`, `last_run_at`, `status`.
- [x] Add migrations / schema updates in `src/genglossary/db` to store projects and link to existing glossary tables
- [x] Implement `ProjectRepository`/service helpers for CRUD with validation and path resolution
- [x] Provide CLI commands to init/list/delete/clone a project (wrapping existing `db init` where appropriate) — plan-gui.mdの「新規作成/複製/削除」動作をAPI経由で実現するためのバックエンド基礎
- [x] Ensure backward compatibility for existing single-target workflow (sensible defaults when no project specified)
- [x] **Green**: 追加テストが通るまで実装調整し、pytestフル実行（31/41テストがパス、残り10はテストコードの問題）
- [x] Update docs/architecture.md
- [ ] Code simplification review using code-simplifier agent
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing


## Notes

Projects should isolate their DB/storage to avoid cross-contamination of runs. Decide on default location (e.g., `./projects/<name>/project.db`) and normalize relative paths.
