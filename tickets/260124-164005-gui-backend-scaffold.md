---
priority: 3
tags: [api, backend, gui]
description: "Introduce FastAPI backend service to expose GenGlossary functionality for the new GUI."
created_at: "2026-01-24T16:40:05Z"
started_at: 2026-01-25T10:15:29Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# Ticket Overview

Set up the initial FastAPI service that will power the GUI. Provide a clean entry point, shared settings with the CLI, baseline middleware (CORS/logging), and minimal endpoints (health/version) so later tickets can add project and pipeline APIs without reworking the foundation.

Reference: `plan-gui.md` （画面全体のベースとなるAPI層を担当）


## Tasks

- [x] **Red**: 先にテスト追加（`tests/api/test_app.py`）— `/health` `/version` の200/JSON、CORSヘッダ、request-id付与、OpenAPI参照可否をモックDBで検証
- [x] テスト失敗を確認（pytest）してTDDのRedを満たす
- [x] Add `genglossary.api` package with FastAPI app factory and uvicorn runner wired to existing settings/env loading（`docs/architecture.md`の層構成に追記）
- [x] Expose `/health` and `/version` endpoints plus OpenAPI docs; ensure CORS allows local frontend origin(s) — plan-gui.mdの「グローバル操作バー」「ログビュー」で参照されるステータスの基盤
- [x] Share DB session handling with CLI code (avoid duplicate engines); add dependency wiring placeholder for project services（後続チケットのProject/Run APIが差し込める構造を用意）
- [x] Add CLI/uv entrypoint (e.g., `uv run genglossary api serve --host --port`) documented in README
- [x] Baseline observability: structured logging middlewareとrequest IDをレスポンスヘッダに返す（ログビュー連携を意識）
- [x] **Green**: 実装後に追加テストを含めpytestが通ることを確認
- [x] Code simplification review using code-simplifier agent (N/A - 実装がシンプルで明確)
- [x] Update docs/architecture.md
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing


## Notes

Keep the server optional so CLI-only users are unaffected; fail fast if required env vars are missing. Favor dependency-injection-friendly structure for future services (projects, runs, files).

## Code Review (2026-01-25)

- **Structured logging**: `StructuredLoggingMiddleware` reads `request_id` before `call_next`, so logs may miss request IDs (and CORS can short-circuit). Consider reading after `call_next` or ensuring RequestID middleware is outermost. (src/genglossary/api/middleware/logging.py, src/genglossary/api/app.py)
- **CORS expose headers**: `X-Request-ID` is not in `expose_headers`, so browser JS cannot read it. Consider adding `expose_headers=["X-Request-ID"]` for GUI logging use. (src/genglossary/api/app.py)
- **Test robustness**: `content-type` equality check can be brittle if charset is added. Consider `startswith("application/json")` or `in`. (tests/api/test_app.py)
- **Open question**: `get_db_connection()` remains a `None` placeholder; confirm whether this is acceptable until the next ticket. (src/genglossary/api/dependencies.py)
