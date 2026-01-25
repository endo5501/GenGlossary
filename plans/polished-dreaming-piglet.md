# GUI API Operations Runner 残りタスク実装計画

## 概要

`tickets/260124-164011-gui-api-operations-runner.md` の残りタスクを完了させる計画。

## 残りタスク一覧

1. PipelineExecutorに実際のパイプラインロジック統合
2. API統合テストの修正（SQLite threading問題解決）
3. docs/architecture.md更新
4. code-simplifier agentによるレビュー
5. 静的解析（pyright）とフルテストスイート実行

---

## フェーズ1: RunManager接続管理改善

### 問題
- `RunManager` が `sqlite3.Connection` をコンストラクタで受け取り、バックグラウンドスレッドで共有
- APIリクエスト終了時に `get_project_db()` が接続を閉じるが、スレッドはまだ動作中
- 結果: Segmentation Fault

### 解決策
`db_path` を渡し、バックグラウンドスレッド内で独自の接続を作成

### 変更ファイル

**`src/genglossary/runs/manager.py`**
```python
class RunManager:
    def __init__(self, db_path: str):  # 接続→パスに変更
        self.db_path = db_path
        # ...

    def _execute_run(self, run_id: int, scope: str) -> None:
        conn = get_connection(self.db_path)  # スレッド内で新規接続
        try:
            # ... パイプライン実行
        finally:
            conn.close()  # スレッド内で閉じる
```

**`src/genglossary/api/dependencies.py`**
```python
def get_project_db_path(project: Project = Depends(get_project_by_id)) -> str:
    return project.db_path
```

**`src/genglossary/api/routers/runs.py`**
```python
def get_run_manager(db_path: str = Depends(get_project_db_path)) -> RunManager:
    return RunManager(db_path)
```

### テスト修正
- `tests/runs/test_manager.py` のfixtureを `db_path` を渡す方式に変更

---

## フェーズ2: PipelineExecutor実装（TDD）

### ステップ2.1: テスト作成（Red）

**`tests/runs/test_executor.py`** を新規作成

```python
class TestPipelineExecutorFull:
    def test_full_scope_executes_all_steps(self):
        """full scopeは全ステップを実行"""

    def test_full_scope_respects_cancellation(self):
        """キャンセル時は途中で停止"""

class TestPipelineExecutorFromTerms:
    def test_from_terms_skips_document_loading(self):
        """from_termsはドキュメント読み込みをスキップ"""

class TestPipelineExecutorProvisionalToRefined:
    def test_provisional_to_refined_starts_from_review(self):
        """provisional_to_refinedは精査から開始"""

class TestPipelineExecutorProgress:
    def test_progress_updates_are_logged(self):
        """進捗がlog_queueに送信される"""
```

### ステップ2.2: 実装（Green）

**`src/genglossary/runs/executor.py`**

CLIの `_generate_glossary_with_db()` (cli.py:148-321) のロジックを再利用:

| Scope | 実行ステップ |
|-------|------------|
| `full` | 1→2→3→4→5 (全パイプライン) |
| `from_terms` | 3→4→5 (既存termsを使用) |
| `provisional_to_refined` | 4→5 (既存provisionalを使用) |

```python
class PipelineExecutor:
    def execute(self, conn, scope, cancel_event, log_queue, run_id=None):
        if scope == "full":
            self._execute_full(...)
        elif scope == "from_terms":
            self._execute_from_terms(...)
        elif scope == "provisional_to_refined":
            self._execute_provisional_to_refined(...)

    def _execute_full(self, cancel_event, log_queue):
        # Step 1: DocumentLoader
        # Step 2: TermExtractor
        # Step 3-5: _execute_from_terms()

    def _execute_from_terms(self, cancel_event, log_queue):
        # Step 3: GlossaryGenerator
        # Step 4-5: _execute_provisional_to_refined()

    def _execute_provisional_to_refined(self, cancel_event, log_queue):
        # Step 4: GlossaryReviewer
        # Step 5: GlossaryRefiner
```

### モック戦略
- LLMクライアントをモック（`@patch("genglossary.llm.factory.create_llm_client")`）
- 各コンポーネント（TermExtractor等）の出力をモック

---

## フェーズ3: API統合テスト再実装

**`tests/api/routers/test_runs.py`** を新規作成

### テストケース

```python
class TestStartRun:
    def test_start_run_creates_run_record(self):
    def test_start_run_returns_409_when_already_running(self):
    def test_start_run_with_different_scopes(self):

class TestCancelRun:
    def test_cancel_run_updates_status(self):
    def test_cancel_nonexistent_run_returns_404(self):

class TestListRuns:
    def test_list_runs_returns_history(self):

class TestGetRun:
    def test_get_run_returns_details(self):
    def test_get_run_returns_404_for_missing(self):

class TestGetCurrentRun:
    def test_get_current_run_returns_active(self):
    def test_get_current_run_returns_404_when_none(self):
```

### テストの同期戦略
- `PipelineExecutor.execute` をモックして即座に完了
- `time.sleep()` + `thread.join()` でスレッド完了を待機

---

## フェーズ4: docs/architecture.md更新

### 追加セクション

`### 8. runs/ - Run管理` を追加:

- **役割**: バックグラウンドパイプライン実行の管理
- **manager.py**: `db_path`を受け取り、スレッド内で接続を作成
- **executor.py**: CLIパイプラインコンポーネントの再利用
- **スレッディングアーキテクチャ図**
- **Runs APIエンドポイント一覧**

---

## フェーズ5: 最終確認

### code-simplifier agentレビュー
- 重複コードの特定
- リファクタリング提案

### 静的解析とテスト
```bash
uv run pyright
uv run pytest
```

---

## 重要ファイル

| ファイル | 変更内容 |
|---------|---------|
| `src/genglossary/runs/manager.py` | db_path方式に変更 |
| `src/genglossary/runs/executor.py` | パイプラインロジック統合 |
| `src/genglossary/api/dependencies.py` | get_project_db_path追加 |
| `src/genglossary/api/routers/runs.py` | 依存性変更 |
| `tests/runs/test_manager.py` | fixture修正 |
| `tests/runs/test_executor.py` | 新規作成 |
| `tests/api/routers/test_runs.py` | 新規作成 |
| `docs/architecture.md` | Run管理セクション追記 |

---

## 検証方法

1. **単体テスト**: `uv run pytest tests/runs/`
2. **API統合テスト**: `uv run pytest tests/api/routers/test_runs.py`
3. **フルテストスイート**: `uv run pytest`
4. **静的解析**: `uv run pyright`
5. **手動確認**: FastAPIサーバーを起動し、curlでRuns APIをテスト

```bash
# サーバー起動
uv run uvicorn genglossary.api.app:app --reload

# Run開始
curl -X POST http://localhost:8000/api/projects/1/runs \
  -H "Content-Type: application/json" \
  -d '{"scope": "full"}'

# Run一覧
curl http://localhost:8000/api/projects/1/runs
```
