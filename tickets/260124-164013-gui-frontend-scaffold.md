---
priority: 6
tags: [frontend, build, ux]
description: "Bootstrap the web frontend (React/Vite) with design system, routing, API client, and shared layout shell."
created_at: "2026-01-24T16:40:13Z"
started_at: 2026-01-26T15:09:13Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# Ticket Overview

Create the GUI frontend foundation: tooling, folder structure, routing, design tokens, API client, and the global chrome (top bar + sidebar + log drawer placeholders). This sets the visual and technical baseline for later feature screens.

Reference: `plan-gui.md` 全画面の共通レイアウト（グローバル操作バー + 左ナビ + ログビュー）を支える足場。


## Tasks

- [ ] **Red**: 先にフロントテスト追加（`frontend/src/__tests__/app-shell.test.tsx` など）— ルーティング初期化、レイアウト枠の要素存在、APIクライアントのベースURL設定をRTL/Vitestで失敗させる
- [ ] テスト失敗を確認（Red完了）
- [ ] Initialize React + TypeScript project (Vite) under `frontend/` with pnpm and lint/prettier configs aligned to repo style
- [ ] Configure Mantine as design system with custom theme tokens, avoiding default purple bias; set typography/color primitives（`docs/architecture.md` にUIスタックを追記）— plan-guiの意図的なビジュアルを反映
- [ ] Add routing (TanStack Router or React Router) and query/data layer (TanStack Query) with API base URL env
- [ ] Implement shared layout shell: global top bar (project title/status slots), left nav rail, main content area, bottom log panel placeholder
- [ ] Build API client wrapper with auth-less base headers, error handling, and type-safe responses
- [ ] Add storybook or component preview script if lightweight, otherwise document UI tokens in README
- [ ] **Green**: 追加テストを含む lint/build/test が通ることを確認
- [ ] Code simplification review using code-simplifier agent
- [ ] Code review by codex MCP
- [ ] Update docs/architecture.md
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing


## Notes

Keep backend/frontend dev servers co-exist (different ports, CORS ready). Favor bold, intentional styling per frontend guidelines. Document how to run `pnpm dev` alongside FastAPI.
