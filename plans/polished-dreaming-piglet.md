# コードレビュー指摘事項の修正計画

## ステータス: ✅ 実装完了 (2026-01-26)

すべての問題が修正され、テストが追加されました。
- テストコミット: d355101
- 実装コミット: ca3fd79
- すべてのテスト（637個）がパス

## 概要

`tickets/260124-164011-gui-api-operations-runner.md` の Code Review (2026-01-25) で指摘された問題を修正する計画。

---

## 問題一覧と優先度

| 優先度 | 問題 | 影響 |
|--------|------|------|
| **Critical** | RunManagerがリクエスト毎に新規生成 | キャンセル・ログ取得が機能しない |
| **High** | 入力ディレクトリが `"."` 固定 | 誤ったドキュメントを処理 |
| **High** | LLM設定がプロジェクト設定を無視 | 常にollamaを使用 |
| **Medium** | SSE完了シグナルがない | ストリームが閉じない |
| **Medium** | 再実行時にUNIQUE制約違反 | Runがfailedになる |

---

## フェーズ1: RunManagerシングルトン化 (Critical)

### 問題の詳細
- `get_run_manager()` が毎回新しい `RunManager` インスタンスを生成
- キャンセル時: 別インスタンスの `_cancel_event.set()` を呼ぶため、実行中スレッドには届かない
- ログ取得時: 別インスタンスの `_log_queue` を参照するため、空のまま

### 解決策: プロジェクト単位のレジストリパターン

**`src/genglossary/api/dependencies.py`**
```python
from threading import Lock
from genglossary.runs.manager import RunManager

_run_manager_registry: dict[str, RunManager] = {}
_registry_lock = Lock()

def get_run_manager(project: Project = Depends(get_project_by_id)) -> RunManager:
    """Get or create RunManager instance for the project (singleton per project)."""
    with _registry_lock:
        if project.db_path not in _run_manager_registry:
            _run_manager_registry[project.db_path] = RunManager(
                db_path=project.db_path,
                doc_root=project.doc_root,
                llm_provider=project.llm_provider,
                llm_model=project.llm_model,
            )
        return _run_manager_registry[project.db_path]
```

**`src/genglossary/api/routers/runs.py`**
- `get_run_manager` を `dependencies.py` から import に変更
- ローカルの `get_run_manager` 関数を削除

### 変更ファイル
- `src/genglossary/api/dependencies.py` - レジストリ追加
- `src/genglossary/api/routers/runs.py` - import変更

---

## フェーズ2: プロジェクト設定の反映 (High)

### 問題の詳細
- `executor.py` の `load_directory(".")` がハードコード
- `PipelineExecutor(provider="ollama")` が固定

### 解決策: RunManager経由でプロジェクト設定を渡す

**`src/genglossary/runs/manager.py`**
```python
class RunManager:
    def __init__(
        self,
        db_path: str,
        doc_root: str = ".",
        llm_provider: str = "ollama",
        llm_model: str = "",
    ):
        self.db_path = db_path
        self.doc_root = doc_root
        self.llm_provider = llm_provider
        self.llm_model = llm_model
        # ...

    def _execute_run(self, run_id: int, scope: str) -> None:
        # ...
        executor = PipelineExecutor(
            provider=self.llm_provider,
            model=self.llm_model,
        )
        executor.execute(
            conn, scope, self._cancel_event, self._log_queue,
            doc_root=self.doc_root,
        )
```

**`src/genglossary/runs/executor.py`**
```python
class PipelineExecutor:
    def __init__(self, provider: str = "ollama", model: str = ""):
        self._llm_client = create_llm_client(provider=provider, model=model)

    def execute(self, conn, scope, cancel_event, log_queue, doc_root: str = "."):
        # doc_rootを各メソッドに渡す

    def _execute_full(self, ..., doc_root: str):
        documents = loader.load_directory(doc_root)  # "." → doc_root
```

### 変更ファイル
- `src/genglossary/runs/manager.py` - コンストラクタ拡張、executor呼び出し変更
- `src/genglossary/runs/executor.py` - doc_root/modelパラメータ追加
- `src/genglossary/llm/factory.py` - model引数対応（必要に応じて）

---

## フェーズ3: SSE完了シグナル追加 (Medium)

### 問題の詳細
- Run完了後に `log_queue.put(None)` が呼ばれない
- SSEクライアントはkeepaliveを受け続け、完了を検知できない

### 解決策

**`src/genglossary/runs/manager.py`**
```python
def _execute_run(self, run_id: int, scope: str) -> None:
    conn = get_connection(self.db_path)
    try:
        # ... パイプライン実行
    except Exception as e:
        # ... エラー処理
    finally:
        # Send completion signal to close SSE stream
        self._log_queue.put(None)
        conn.close()
```

### 変更ファイル
- `src/genglossary/runs/manager.py` - finallyブロックに追加

---

## フェーズ4: 再実行時のUNIQUE制約対応 (Medium)

### 問題の詳細
- 2回目のRun実行時、既存データでINSERTが失敗
- 影響テーブル: `documents`, `terms_extracted`, `glossary_provisional`, `glossary_refined`

### 解決策: 実行前にスコープに応じてテーブルクリア

**`src/genglossary/runs/executor.py`**
```python
def execute(self, conn, scope, cancel_event, log_queue, doc_root: str = "."):
    # Clear tables before execution
    self._clear_tables_for_scope(conn, scope)
    # ... 既存ロジック

def _clear_tables_for_scope(self, conn: sqlite3.Connection, scope: str) -> None:
    """Clear relevant tables before execution."""
    if scope == "full":
        delete_all_documents(conn)
        delete_all_terms(conn)
        delete_all_provisional(conn)
        delete_all_issues(conn)
        delete_all_refined(conn)
    elif scope == "from_terms":
        delete_all_provisional(conn)
        delete_all_issues(conn)
        delete_all_refined(conn)
    elif scope == "provisional_to_refined":
        delete_all_issues(conn)
        delete_all_refined(conn)
```

**`src/genglossary/db/document_repository.py`** (新規関数)
```python
def delete_all_documents(conn: sqlite3.Connection) -> None:
    """Delete all documents."""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM documents")
    conn.commit()
```

### 変更ファイル
- `src/genglossary/runs/executor.py` - クリア処理追加
- `src/genglossary/db/document_repository.py` - delete_all_documents追加

---

## フェーズ5: テスト追加 (TDD)

### 新規テストケース

**`tests/runs/test_manager.py`** (追加)
```python
def test_cancel_run_stops_execution():
    """キャンセルが実行中スレッドに届くことを確認"""

def test_sse_receives_completion_signal():
    """SSEストリームが完了シグナルで閉じることを確認"""
```

**`tests/runs/test_executor.py`** (追加)
```python
def test_executor_uses_doc_root():
    """doc_rootパラメータが使用されることを確認"""

def test_executor_uses_llm_settings():
    """llm_provider/llm_modelが使用されることを確認"""

def test_re_execution_clears_tables():
    """再実行時にテーブルがクリアされることを確認"""
```

**`tests/api/test_dependencies.py`** (新規)
```python
def test_run_manager_singleton_per_project():
    """同一プロジェクトで同じRunManagerインスタンスが返ることを確認"""
```

---

## 変更ファイル一覧

| ファイル | 変更内容 |
|---------|---------|
| `src/genglossary/api/dependencies.py` | RunManagerレジストリ追加 |
| `src/genglossary/api/routers/runs.py` | get_run_managerをimportに変更 |
| `src/genglossary/runs/manager.py` | コンストラクタ拡張、完了シグナル追加 |
| `src/genglossary/runs/executor.py` | doc_root/model対応、テーブルクリア追加 |
| `src/genglossary/db/document_repository.py` | delete_all_documents追加 |
| `src/genglossary/llm/factory.py` | model引数対応（必要に応じて） |
| `tests/runs/test_manager.py` | キャンセル・SSEテスト追加 |
| `tests/runs/test_executor.py` | 設定反映・クリアテスト追加 |
| `tests/api/test_dependencies.py` | シングルトンテスト新規作成 |

---

## 検証方法

### 1. 単体テスト
```bash
uv run pytest tests/runs/ -v
uv run pytest tests/api/test_dependencies.py -v
```

### 2. E2Eテスト（手動）
```bash
# サーバー起動
uv run uvicorn genglossary.api.app:app --reload

# ターミナル1: Run開始
curl -X POST http://localhost:8000/api/projects/1/runs \
  -H "Content-Type: application/json" \
  -d '{"scope": "full"}'

# ターミナル2: SSEログ確認
curl -N http://localhost:8000/api/projects/1/runs/1/logs

# ターミナル3: キャンセル
curl -X DELETE http://localhost:8000/api/projects/1/runs/1

# 再実行テスト（UNIQUE制約確認）
curl -X POST http://localhost:8000/api/projects/1/runs \
  -H "Content-Type: application/json" \
  -d '{"scope": "full"}'
```

### 3. 静的解析
```bash
uv run pyright
uv run pytest
```

---

## Open Questionsへの回答

1. **RunManagerをプロジェクト単位で共有する設計にする前提で良いか？**
   → Yes。レジストリパターンで `db_path` をキーにシングルトン管理

2. **再実行時はテーブルクリアか INSERT OR REPLACE/IGNORE の方針か？**
   → テーブルクリア。古いデータとの混在を防ぎ、データの一貫性を保証

3. **Run実行時の入力ディレクトリは Project.doc_root で固定して良いか？**
   → Yes。プロジェクト作成時に設定された `doc_root` を使用
