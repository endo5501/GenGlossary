# Code Simplification Review 検討結果

**チケット**: `tickets/260124-164008-gui-project-model-storage.md`

## 背景

本チケットの残タスク「Code simplification review using code-simplifier agent」の必要性を評価する。

---

## 追加されたコードの分析

| ファイル | 行数 | 複雑度 | 評価 |
|---------|------|--------|------|
| `models/project.py` | 110 | 低 | Pydanticベストプラクティスに従った簡潔な実装 |
| `db/registry_connection.py` | 69 | 低 | 最小限の実装、シンプル |
| `db/registry_schema.py` | 82 | 低 | 既存の`schema.py`と同じパターン |
| `db/project_repository.py` | 262 | 中 | 他のリポジトリと同じパターンを踏襲 |
| `cli_project.py` | 249 | 中 | 標準的なClickパターン |

**合計**: 約772行の新規コード

## 良い点

1. **一貫したパターン**: 既存コードベースのパターンを踏襲
2. **適切なドキュメント**: 全関数にdocstring付き
3. **シンプルな構造**: 各ファイルが単一責任を持つ
4. **型安全**: Pydanticモデルと型ヒントを活用

## 検出された軽微な改善候補

### 1. CLI内のパス解決ロジックの重複

`cli_project.py` の `init` と `clone` で同じコード:

```python
if registry:
    registry_dir = registry.parent / "projects"
else:
    registry_dir = get_default_registry_path().parent / "projects"
```

**対応**: ヘルパー関数に抽出可能だが、2箇所のみで影響は軽微

### 2. update_project()の空更新ケース

`project_repository.py` 192-194行目:
```python
if not updates:
    # No fields to update, but we still update updated_at
    pass
```

**対応**: このpassは`updates`に必ず`updated_at`が追加されるため実際には実行されない（デッドコード）。削除可能だが影響は軽微。

---

## 実施事項（ユーザー選択）

**決定: code-simplifierエージェントによるレビューを実施**

## 実行計画

### Step 1: Code Simplification Review

code-simplifierエージェントで以下のファイルをレビュー:

| ファイル | 確認観点 |
|---------|---------|
| `src/genglossary/models/project.py` | バリデータの重複、モデル構造 |
| `src/genglossary/db/registry_connection.py` | 既存connection.pyとの一貫性 |
| `src/genglossary/db/registry_schema.py` | 既存schema.pyとの一貫性 |
| `src/genglossary/db/project_repository.py` | CRUD操作の簡素化、デッドコード |
| `src/genglossary/cli_project.py` | パス解決ロジックの重複、エラーハンドリング |

### Step 2: 静的解析

```bash
uv run pyright
```

### Step 3: テスト実行

```bash
uv run pytest
```

注意: `tests/db/test_project_repository.py`に10件のテスト失敗あり（`tmp_path`パラメータ欠落）。修正が必要。

### Step 4: 開発者承認

チケットをクローズ前に承認を取得

---
---

# 以下は実装時の参考計画（アーカイブ）

## アーキテクチャ決定

### 1. プロジェクトレジストリのストレージ

**決定**: 中央SQLiteデータベース `~/.genglossary/registry.db` を使用

**理由**:
- 既存のSQLiteパターンと一貫性がある
- トランザクションサポートによるアトミックなCRUD操作
- スキーマバージョン管理による将来のマイグレーション対応

**ストレージ構造**:
```
~/.genglossary/
├── registry.db           # 中央プロジェクトレジストリ
└── projects/             # デフォルトのプロジェクト保存場所
    ├── my-novel/
    │   └── project.db    # プロジェクト固有のデータ
    └── tech-docs/
        └── project.db
```

### 2. プロジェクト分離戦略

**決定**: 各プロジェクトは独自のDBファイルを持ち、全ての用語集テーブルを含む

**理由**:
- 完全なデータ分離（相互汚染なし）
- 簡単なバックアップ/エクスポート（プロジェクトごとに1ファイル）
- 既存の `genglossary.db` パターンを踏襲

## スキーマ設計

### 中央レジストリ (`~/.genglossary/registry.db`)

```sql
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    doc_root TEXT NOT NULL,           -- ドキュメントディレクトリの絶対パス
    db_path TEXT NOT NULL UNIQUE,     -- project.db の絶対パス
    llm_provider TEXT NOT NULL DEFAULT 'ollama',
    llm_model TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    last_run_at TEXT,                 -- 未実行なら NULL
    status TEXT NOT NULL DEFAULT 'created'  -- created, running, completed, error
);
```

## 実装ファイル

### 新規作成ファイル

| ファイル | 目的 |
|---------|------|
| `src/genglossary/models/project.py` | Project Pydanticモデル |
| `src/genglossary/db/registry_connection.py` | レジストリDB接続管理 |
| `src/genglossary/db/registry_schema.py` | レジストリスキーマ定義 |
| `src/genglossary/db/project_repository.py` | プロジェクトCRUD操作 |
| `src/genglossary/cli_project.py` | プロジェクトCLIコマンド |

### テストファイル

| ファイル | 目的 |
|---------|------|
| `tests/models/test_project.py` | Projectモデルのテスト |
| `tests/db/test_registry_schema.py` | レジストリスキーマのテスト |
| `tests/db/test_project_repository.py` | プロジェクトリポジトリのテスト |
| `tests/test_cli_project.py` | プロジェクトCLI統合テスト |

### 修正ファイル

| ファイル | 変更内容 |
|---------|---------|
| `src/genglossary/db/__init__.py` | 新モジュールのエクスポート |
| `src/genglossary/cli.py` | projectコマンドグループの登録 |
| `docs/architecture.md` | プロジェクトアーキテクチャの文書化 |

## TDD実装順序

### Phase 1: Red - テスト作成

#### 1.1 Projectモデルテスト

```python
# tests/models/test_project.py
def test_project_creation_with_defaults():
    """最小必須フィールドでProjectを作成できる"""

def test_project_status_enum():
    """ProjectStatusは期待値を持つ"""
```

#### 1.2 レジストリスキーマテスト

```python
# tests/db/test_registry_schema.py
def test_initialize_registry_creates_tables():
    """初期化でprojectsテーブルが作成される"""

def test_initialize_registry_is_idempotent():
    """複数回呼び出しても安全"""
```

#### 1.3 プロジェクトリポジトリテスト

```python
# tests/db/test_project_repository.py
class TestCreateProject:
    def test_create_project_returns_id()
    def test_create_project_with_all_fields()
    def test_create_duplicate_name_raises()
    def test_create_duplicate_db_path_raises()

class TestGetProject:
    def test_get_project_by_id()
    def test_get_nonexistent_returns_none()

class TestGetProjectByName:
    def test_get_by_name()
    def test_get_by_name_not_found()

class TestListProjects:
    def test_list_empty()
    def test_list_multiple()

class TestUpdateProject:
    def test_update_llm_settings()
    def test_update_status()
    def test_update_nonexistent_raises()

class TestDeleteProject:
    def test_delete_removes_project()
    def test_delete_nonexistent_does_not_fail()

class TestCloneProject:
    def test_clone_creates_copy()
    def test_clone_nonexistent_raises()
```

#### 1.4 CLIテスト

```python
# tests/test_cli_project.py
class TestProjectInit:
    def test_init_creates_project()
    def test_init_duplicate_name_fails()

class TestProjectList:
    def test_list_empty()
    def test_list_shows_projects()

class TestProjectDelete:
    def test_delete_removes_project()

class TestProjectClone:
    def test_clone_creates_copy()

class TestBackwardCompatibility:
    def test_db_commands_work_without_project()
```

### Phase 2: Green - 実装

1. `src/genglossary/models/project.py` - Pydanticモデル
2. `src/genglossary/db/registry_connection.py` - DB接続
3. `src/genglossary/db/registry_schema.py` - スキーマ初期化
4. `src/genglossary/db/project_repository.py` - CRUD操作
5. `src/genglossary/cli_project.py` - CLIコマンド
6. `src/genglossary/cli.py` に `project` コマンドを登録

### Phase 3: 統合とドキュメント

1. `src/genglossary/db/__init__.py` を更新
2. `docs/architecture.md` を更新

## CLIコマンド

```bash
# プロジェクト作成
genglossary project init my-novel --doc-root ./novel-docs

# プロジェクト一覧
genglossary project list

# プロジェクト削除
genglossary project delete my-novel

# プロジェクト複製
genglossary project clone my-novel my-novel-backup
```

## 後方互換性

- 既存の `db` コマンドは変更なし
- プロジェクト不要で単一DBファイルワークフローを継続可能
- 既存データベースは後からプロジェクトにインポート可能

## 検証手順

1. テスト実行
   ```bash
   uv run pytest tests/models/test_project.py -v
   uv run pytest tests/db/test_registry_schema.py -v
   uv run pytest tests/db/test_project_repository.py -v
   uv run pytest tests/test_cli_project.py -v
   uv run pytest  # 全テスト
   ```

2. 型チェック
   ```bash
   uv run pyright
   ```

3. CLIコマンド動作確認
   ```bash
   uv run genglossary project init test-project --doc-root ./target_docs
   uv run genglossary project list
   uv run genglossary project clone test-project test-project-copy
   uv run genglossary project delete test-project-copy
   uv run genglossary project delete test-project
   ```

4. 後方互換性確認
   ```bash
   uv run genglossary db init --path ./legacy.db
   uv run genglossary db info --db-path ./legacy.db
   ```

## 重要なリファレンスファイル

- `/Users/endo5501/Work/GenGlossary/src/genglossary/db/metadata_repository.py` - リポジトリパターンの参考
- `/Users/endo5501/Work/GenGlossary/src/genglossary/db/schema.py` - スキーマ初期化の参考
- `/Users/endo5501/Work/GenGlossary/src/genglossary/cli_db.py` - CLIコマンドの参考
- `/Users/endo5501/Work/GenGlossary/tests/db/test_metadata_repository.py` - テストパターンの参考
