---
priority: 2
tags: [bug, storage, testing]
description: "Fix project DB path generation inconsistency between CLI and API, and fix test data leaking to production directory"
created_at: "2026-02-08T15:21:06Z"
started_at: 2026-02-08T15:31:57Z # Do not modify manually
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

- `src/genglossary/api/routers/projects.py` — `_generate_db_path()`, `_generate_doc_root()`, `_cleanup_doc_root()`, `_create_project_with_cleanup()`
- `src/genglossary/cli_project.py` — `_get_project_db_path()`
- `tests/conftest.py` — ルートレベルのテスト隔離フィクスチャ追加
- `tests/api/conftest.py` — `isolate_registry` フィクスチャ削除

## 設計

### 1. テスト隔離 (tests/conftest.py)

ルートレベルに autouse フィクスチャを追加し、全テストで `GENGLOSSARY_DATA_DIR` と `GENGLOSSARY_REGISTRY_PATH` を `tmp_path` 配下に向ける。

```python
@pytest.fixture(autouse=True)
def isolate_data_dir(tmp_path, monkeypatch):
    test_data_dir = tmp_path / "genglossary_data"
    test_data_dir.mkdir()
    monkeypatch.setenv("GENGLOSSARY_DATA_DIR", str(test_data_dir))
    monkeypatch.setenv("GENGLOSSARY_REGISTRY_PATH", str(test_data_dir / "registry.db"))
```

`tests/api/conftest.py` の `isolate_registry` はルートに統合されるため削除。
pytest の `tmp_path` は直近3回分のみ保持し古い分は自動削除されるため、残骸蓄積の心配なし。

### 2. CLI の DB パス生成をフラット方式に統一 (cli_project.py)

`_get_project_db_path()` を API と同じ `{名前}_{UUID}.db` 方式に変更。

```python
def _get_project_db_path(registry, project_name):
    projects_dir = _get_projects_dir(registry)
    projects_dir.mkdir(parents=True, exist_ok=True)
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in project_name)
    unique_id = uuid4().hex[:8]
    db_path = projects_dir / f"{safe_name}_{unique_id}.db"
    return db_path.resolve()
```

サニタイズロジックは CLI/API で重複するが、2箇所のみ・1行のロジックなので共通化しない（YAGNI）。

### 3. API の `_generate_doc_root()` 廃止 (api/routers/projects.py)

Web API ではドキュメントは DB に直接保存されるため、`doc_root` ディレクトリの自動生成は不要。

- `doc_root` 未指定時は空文字 `""` を registry に保存
- `_generate_doc_root()` 関数を削除
- `_cleanup_doc_root()` 関数を削除
- `_create_project_with_cleanup()` の `doc_root_auto_generated` パラメータと関連ロジックを削除
- registry スキーマの `doc_root TEXT NOT NULL` はそのまま（空文字で対応、スキーマ変更不要）

### 4. テスト残骸のクリーンアップ

全コード変更・テスト完了後に `~/.genglossary/` を削除。次回プロジェクト作成時に自動再作成される。

```bash
rm -rf ~/.genglossary
```

## Tasks

- [ ] テスト隔離: ルート `tests/conftest.py` に `isolate_data_dir` autouse フィクスチャ追加
- [ ] テスト隔離: `tests/api/conftest.py` の `isolate_registry` 削除
- [ ] テスト実行して既存テストが全パスすることを確認
- [ ] CLI 統一: `cli_project.py` の `_get_project_db_path()` をフラット方式に変更
- [ ] API 廃止: `_generate_doc_root()`, `_cleanup_doc_root()` 削除、`doc_root` 未指定時は空文字
- [ ] テスト実行して全パスすることを確認
- [ ] クリーンアップ: `~/.genglossary/` 削除
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

- 開発中のツールのため `~/.genglossary/` 配下は全削除可能
- `provisional.py` が `DocumentLoader().load_directory(project.doc_root)` でファイルシステムから直接読んでいる問題は別チケットで対応
