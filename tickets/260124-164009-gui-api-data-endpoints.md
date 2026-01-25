---
priority: 4.5
tags: [api, crud, gui]
description: "Expose Terms/Provisional/Issues/Refined/Files data as REST endpoints for GUI consumption."
created_at: "2026-01-25T00:00:00Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# Ticket Overview

Provide RESTful API endpoints for all data entities used in the GUI. Leverage existing
repository classes (term_repository, provisional_repository, etc.) to serve CRUD
operations. This bridges the gap between the operations API (run/stop) and the
frontend data needs.

Reference: `plan-gui.md` - Terms/Provisional/Issues/Refined/Files各画面のデータ取得・編集に必要


## Tasks

- [ ] **Red**: テスト追加（`tests/api/test_data_endpoints.py`）— 各エンドポイントのレスポンス検証
- [ ] テスト失敗を確認（Red完了）
- [ ] Terms API
  - GET /api/projects/{project_id}/terms — 一覧取得
  - GET /api/projects/{project_id}/terms/{term_id} — 詳細取得
  - PATCH /api/projects/{project_id}/terms/{term_id} — 編集
  - DELETE /api/projects/{project_id}/terms/{term_id} — 除外
  - POST /api/projects/{project_id}/terms — 手動追加
- [ ] Provisional API
  - GET /api/projects/{project_id}/provisional — 一覧取得
  - PATCH /api/projects/{project_id}/provisional/{entry_id} — 定義・confidence編集
  - POST /api/projects/{project_id}/provisional/{entry_id}/regenerate — 単一再生成
- [ ] Issues API
  - GET /api/projects/{project_id}/issues — 一覧取得（issue_typeフィルタ対応）
- [ ] Refined API
  - GET /api/projects/{project_id}/refined — 一覧取得
  - GET /api/projects/{project_id}/refined/export-md — Markdownエクスポート
- [ ] Files API
  - GET /api/projects/{project_id}/files — 一覧取得
  - POST /api/projects/{project_id}/files — ファイル追加
  - DELETE /api/projects/{project_id}/files/{file_id} — ファイル削除
  - POST /api/projects/{project_id}/files/diff-scan — 差分スキャン
- [ ] 既存repositoryクラスを呼び出すservice層を作成
- [ ] **Green**: テスト通過確認
- [ ] Code simplification review using code-simplifier agent
- [ ] Update docs/architecture.md
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing


## Notes

既存の `cli_db.py` の実装パターンを参考に、repository層を直接呼び出す。
プロジェクトごとのDB分離を考慮した接続管理が必要。

Dependencies: Tickets #1 (backend scaffold), #2 (project model) must be completed first.
