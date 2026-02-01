---
priority: 2
tags: [backend, db, refactoring]
description: "Additional timestamp consistency improvements"
created_at: "2026-02-01T00:12:29Z"
started_at: 2026-02-01T00:17:11Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# Additional timestamp consistency improvements

## 概要

タイムスタンプ形式の統一修正に伴い、以下の追加改善が必要です。

## 関連ファイル

- `src/genglossary/db/runs_repository.py`
- `src/genglossary/db/schema.py:74`
- `src/genglossary/runs/manager.py`

## 改善点

### 1. `created_at` のタイムスタンプ形式統一 (Medium)
- 現状: SQLite の `datetime('now')` を使用（スペース区切り、タイムゾーンなし）
- 改善: Python の `datetime.now(timezone.utc).isoformat(timespec="seconds")` に統一

### 2. 時間ソースの統一 (Medium)
- 現状: `created_at` は SQLite クロック、`started_at`/`finished_at` は Python クロック
- 改善: すべてのタイムスタンプを同一のソース（Python）に統一

### 3. naive datetime の検証 (Low)
- 現状: `update_run_status` は naive datetime を受け付ける
- 改善: UTC datetime のみを受け付けるガードを追加

### 4. `update_run_status_if_active` のインターフェース統一
- 現状: 内部で `datetime.now(timezone.utc)` を直接使用
- 改善: `finished_at: datetime | None = None` 引数を追加し、`update_run_status` と同じパターンに統一

## Tasks

- [x] Update `create_run` to use Python UTC timestamp for `created_at`
- [x] Update schema default or remove it
- [x] Add validation for timezone-aware datetime in `update_run_status`
- [x] Unify `update_run_status_if_active` interface with `update_run_status`
- [x] Add tests
- [x] Commit
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Update docs/architecture/*.md
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing

## Notes

- 元チケット: 260131-151313-timestamp-format-mismatch
- Codex レビュー結果より
