---
priority: 4.5
tags: [api, crud, gui]
description: "Expose Terms/Provisional/Issues/Refined/Files data as REST endpoints for GUI consumption."
created_at: "2026-01-25T00:00:00Z"
started_at: 2026-01-25T11:56:17Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# Ticket Overview

Provide RESTful API endpoints for all data entities used in the GUI. Leverage existing
repository classes (term_repository, provisional_repository, etc.) to serve CRUD
operations. This bridges the gap between the operations API (run/stop) and the
frontend data needs.

Reference: `plan-gui.md` - Terms/Provisional/Issues/Refined/Files各画面のデータ取得・編集に必要


## Tasks

- [x] **Red**: テスト追加（`tests/api/test_dependencies.py`, `tests/api/routers/test_*.py`）— 各エンドポイントのレスポンス検証
- [x] テスト失敗を確認（Red完了）
- [x] Terms API
  - GET /api/projects/{project_id}/terms — 一覧取得
  - GET /api/projects/{project_id}/terms/{term_id} — 詳細取得
  - PATCH /api/projects/{project_id}/terms/{term_id} — 編集
  - DELETE /api/projects/{project_id}/terms/{term_id} — 除外
  - POST /api/projects/{project_id}/terms — 手動追加
- [x] Provisional API
  - GET /api/projects/{project_id}/provisional — 一覧取得
  - PATCH /api/projects/{project_id}/provisional/{entry_id} — 定義・confidence編集
  - POST /api/projects/{project_id}/provisional/{entry_id}/regenerate — 単一再生成
- [x] Issues API
  - GET /api/projects/{project_id}/issues — 一覧取得（issue_typeフィルタ対応）
  - GET /api/projects/{project_id}/issues/{issue_id} — 詳細取得
- [x] Refined API
  - GET /api/projects/{project_id}/refined — 一覧取得
  - GET /api/projects/{project_id}/refined/{term_id} — 詳細取得
  - GET /api/projects/{project_id}/refined/export-md — Markdownエクスポート
- [x] Files API
  - GET /api/projects/{project_id}/files — 一覧取得
  - GET /api/projects/{project_id}/files/{file_id} — 詳細取得
  - POST /api/projects/{project_id}/files — ファイル追加
  - DELETE /api/projects/{project_id}/files/{file_id} — ファイル削除
  - POST /api/projects/{project_id}/files/diff-scan — 差分スキャン
- [x] Repositoryクラスを直接呼び出すRouter実装（service層は不要と判断）
- [x] **Green**: テスト通過確認（571 tests passed）
- [x] Code simplification review using code-simplifier agent
- [x] Update docs/architecture.md
- [x] Run static analysis (`pyright`) before closing and pass all tests (0 errors)
- [x] Run tests (`uv run pytest`) before closing and pass all tests (571 passed)
- [ ] Get developer approval before closing


## Notes

既存の `cli_db.py` の実装パターンを参考に、repository層を直接呼び出す。
プロジェクトごとのDB分離を考慮した接続管理が必要。

Dependencies: Tickets #1 (backend scaffold), #2 (project model) must be completed first.

## Code Review (2026-01-25)

### Findings (対応済み)
- [✓ FIXED] [重大] `src/genglossary/api/routers/files.py:108-119` パストラバーサル脆弱性 → `resolve()` と `relative_to()` で検証実装 (commit: 5ebec69)
- [✓ FIXED] [高] UNIQUE制約違反の未処理 → `sqlite3.IntegrityError` をキャッチして409を返すように実装 (commit: 5ebec69)
- [✓ FIXED] [低] テストレジストリパス固定 → autouse fixture を追加 (commit: 4191166)

### Findings (別チケット対応)
- [→ 別チケット] [中] `src/genglossary/api/routers/provisional.py:101-128` regenerate TODO → チケット #260125-125901-api-provisional-regenerate に切り出し
- [→ 別チケット] [低] `tests/api/routers/test_provisional.py:172-182` regenerate テスト不足 → 同上

### Questions (回答済み)
- DELETE は「対象が存在しなくても 204」でよい方針ですか？ → **404を返すように実装** (commit: 5ebec69)
- PATCH は部分更新を許容しない前提ですか？ → **現状維持（全フィールド必須）**
