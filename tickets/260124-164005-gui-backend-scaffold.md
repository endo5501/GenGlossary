---
priority: 3
tags: [api, backend, gui]
description: "Introduce FastAPI backend service to expose GenGlossary functionality for the new GUI."
created_at: "2026-01-24T16:40:05Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# Ticket Overview

Set up the initial FastAPI service that will power the GUI. Provide a clean entry point, shared settings with the CLI, baseline middleware (CORS/logging), and minimal endpoints (health/version) so later tickets can add project and pipeline APIs without reworking the foundation.

Reference: `plan-gui.md` （画面全体のベースとなるAPI層を担当）


## Tasks

- [ ] **Red**: 先にテスト追加（`tests/api/test_app.py`）— `/health` `/version` の200/JSON、CORSヘッダ、request-id付与、OpenAPI参照可否をモックDBで検証
- [ ] テスト失敗を確認（pytest）してTDDのRedを満たす
- [ ] Add `genglossary.api` package with FastAPI app factory and uvicorn runner wired to existing settings/env loading（`docs/architecture.md`の層構成に追記）
- [ ] Expose `/health` and `/version` endpoints plus OpenAPI docs; ensure CORS allows local frontend origin(s) — plan-gui.mdの「グローバル操作バー」「ログビュー」で参照されるステータスの基盤
- [ ] Share DB session handling with CLI code (avoid duplicate engines); add dependency wiring placeholder for project services（後続チケットのProject/Run APIが差し込める構造を用意）
- [ ] Add CLI/uv entrypoint (e.g., `uv run genglossary api serve --host --port`) documented in README
- [ ] Baseline observability: structured logging middlewareとrequest IDをレスポンスヘッダに返す（ログビュー連携を意識）
- [ ] **Green**: 実装後に追加テストを含めpytestが通ることを確認
- [ ] Code simplification review using code-simplifier agent
- [ ] Update docs/architecture.md
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing


## Notes

Keep the server optional so CLI-only users are unaffected; fail fast if required env vars are missing. Favor dependency-injection-friendly structure for future services (projects, runs, files).
