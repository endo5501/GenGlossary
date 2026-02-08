---
priority: 2
tags: [bug, storage, testing]
description: "Fix project DB path generation inconsistency between CLI and API, and fix test data leaking to production directory"
created_at: "2026-02-08T15:21:06Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# プロジェクトDBパス生成の不統一とテストデータ漏洩の修正

## 問題概要

### 問題1: CLI と API で DB パス生成方式が異なる

| インターフェース | パス生成方式 | 例 |
|---|---|---|
| **CLI** (`cli_project.py:65-78`) | ネスト: `projects/{名前}/project.db` | `projects/無職転生/project.db` |
| **API** (`api/routers/projects.py:85-99`) | フラット: `projects/{名前}_{UUID}.db` | `projects/無職転生_81c469ae.db` |

API側は `_generate_doc_root()` でドキュメント用ディレクトリ `projects/{名前}/` も作成するため、
DBはフラットに置かれる一方、空のサブディレクトリが残る。

### 問題2: テストDBが本番ディレクトリに漏洩

`tests/api/conftest.py` の `isolate_registry` フィクスチャは `GENGLOSSARY_REGISTRY_PATH` のみ隔離し、
`GENGLOSSARY_DATA_DIR` を隔離していない。テスト実行のたびに `~/.genglossary/projects/` に
テスト用DBが作成されてしまう。

**被害状況:**
- `~/.genglossary/projects/` に 1046個のDBファイル（大半がテスト残骸）
- `Cloned_Project_*.db`, `Minimal_Project_*.db`, `New_Project_*.db` 等がテスト由来
- 実際のプロジェクトは3つのみ（無職転生、ベルリク、崩壊世界の魔法杖職人）

## 対象ファイル

- `src/genglossary/api/routers/projects.py` — `_generate_db_path()`, `_generate_doc_root()`
- `src/genglossary/cli_project.py` — `_get_project_db_path()`
- `tests/api/conftest.py` — `isolate_registry` フィクスチャ

## Tasks

- [ ] `tests/api/conftest.py` の `isolate_registry` に `GENGLOSSARY_DATA_DIR` の隔離を追加
- [ ] テスト残骸防止策: ルートレベル `tests/conftest.py` に `GENGLOSSARY_DATA_DIR` を `tmp_path` に向ける autouse フィクスチャを追加し、全テストで本番ディレクトリへの書き込みを防止する
- [ ] テストを実行し、テストDBが `tmp_path` 配下に作成されることを確認（`~/.genglossary/` に新規ファイルが増えないことを検証）
- [ ] CLI と API の DB パス生成方式を統一（API側をネスト構造に合わせる方向を検討）
- [ ] `~/.genglossary/projects/` のテスト残骸ファイルを手動クリーンアップ
- [ ] Commit
- [ ] Run static analysis (`pyright`) before reviewing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before reviewing and pass all tests (No exceptions)
- [ ] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Update docs (glob: "*.md" in ./docs/architecture)
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## Notes

- 開発中のツールのため `~/.genglossary/` 配下のファイルは全削除可能
- DB パス統一の方向性はCLI側のネスト構造 (`projects/{名前}/project.db`) に合わせるのが自然
  - API の `_generate_db_path()` を修正し、ネスト構造に変更
  - `_generate_doc_root()` も同じディレクトリ内でドキュメントを管理する形に
- registry.db にはプロジェクトの `db_path` が絶対パスで保存されているため、
  パス変更時は既存レコードのマイグレーションも必要（ただし全削除前提なら不要）
- テスト残骸防止の方針:
  - ルート `tests/conftest.py` に autouse フィクスチャで `GENGLOSSARY_DATA_DIR` と `GENGLOSSARY_REGISTRY_PATH` を `tmp_path` 配下に向ける
  - これにより、API テスト以外（CLI テスト等が将来追加された場合）でも本番ディレクトリを汚さない
  - `tests/api/conftest.py` の `isolate_registry` は必要に応じてルートフィクスチャと統合または削除
