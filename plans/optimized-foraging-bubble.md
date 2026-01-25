# コードレビュー（2回目）修正計画

## 概要

チケット `260124-164011-gui-api-operations-runner` に対するコードレビュー（2回目）の全指摘を修正する。

## 修正対象

| # | 優先度 | 指摘 | ファイル |
|---|--------|------|----------|
| 1 | 必須 | ドキュメント無し時のエラーステータス | `executor.py` |
| 2 | High | ログがrun単位で分離されていない | `manager.py`, `runs.py` |
| 3 | Medium | RunManagerレジストリの設定更新 | `dependencies.py` |
| 4 | Low | テストモックの問題 | `test_manager.py` |

## 実装計画

### Phase 1: ドキュメント無し時のエラー（必須）

**問題**: `_execute_full`でドキュメントがない場合に早期リターンするが、例外を発生させていないため`completed`ステータスになる

**修正ファイル**:
- `src/genglossary/runs/executor.py` (112-114行目)

**変更内容**:
```python
# Before
if not documents:
    log_queue.put({"level": "error", "message": "No documents found"})
    return

# After
if not documents:
    log_queue.put({"level": "error", "message": "No documents found"})
    raise RuntimeError("No documents found in doc_root")
```

**テスト追加**:
- `tests/runs/test_executor.py`: `test_full_scope_raises_error_when_no_documents`
- `tests/runs/test_manager.py`: `test_run_sets_failed_status_when_no_documents`

---

### Phase 2: ログのrun_id対応（High）

**問題**: プロジェクト単位の単一キューを使用しており、run_idごとにログをフィルタリングしていない

**修正ファイル**:
- `src/genglossary/runs/executor.py` - `execute()`に`run_id`パラメータ追加、全ログにrun_id付与
- `src/genglossary/runs/manager.py` - executorにrun_idを渡す、完了シグナルにrun_id付与
- `src/genglossary/api/routers/runs.py` - SSEでrun_idフィルタリング

**executor.py変更**:
```python
def execute(
    self,
    conn: sqlite3.Connection,
    scope: str,
    cancel_event: Event,
    log_queue: Queue,
    doc_root: str = ".",
    run_id: int | None = None,  # 追加
) -> None:
    log_queue.put({
        "run_id": run_id,
        "level": "info",
        "message": f"Starting pipeline execution: {scope}"
    })
```

**manager.py変更**:
```python
executor.execute(
    conn, scope, self._cancel_event, self._log_queue,
    doc_root=self.doc_root,
    run_id=run_id,  # 追加
)

# 完了シグナル
self._log_queue.put({"run_id": run_id, "complete": True})  # None → dict形式に変更
```

**runs.py変更**:
```python
# SSEでrun_idフィルタリング
if msg_run_id is not None and msg_run_id != run_id:
    try:
        log_queue.put_nowait(log_msg)
    except Full:
        pass
    continue
```

**テスト追加**:
- `tests/runs/test_manager.py`: `test_logs_include_run_id`, `test_completion_signal_includes_run_id`

---

### Phase 3: RunManagerレジストリ更新（Medium）

**問題**: RunManagerが一度作成されると、プロジェクト設定変更が反映されない

**修正ファイル**:
- `src/genglossary/api/dependencies.py` (119-128行目)

**変更内容**:
```python
def get_run_manager(project: Project = Depends(get_project_by_id)) -> RunManager:
    with _registry_lock:
        existing = _run_manager_registry.get(project.db_path)

        if existing is not None:
            # 設定が変更されていないか確認
            settings_match = (
                existing.doc_root == project.doc_root
                and existing.llm_provider == project.llm_provider
                and existing.llm_model == project.llm_model
            )
            if settings_match:
                return existing

            # 実行中のRunがある場合は再作成しない
            if existing.get_active_run() is not None:
                return existing

        # 新しいRunManagerを作成
        _run_manager_registry[project.db_path] = RunManager(...)
        return _run_manager_registry[project.db_path]
```

**テスト追加**:
- `tests/api/test_dependencies.py`（新規）: 設定変更時の再作成テスト

---

### Phase 4: テストモック修正（Low）

**問題**: `test_sse_receives_completion_signal`のモックが`doc_root`引数を受け取れない

**修正ファイル**:
- `tests/runs/test_manager.py`

**変更内容**:
```python
# Before
def mock_execute(conn, scope, cancel_event, log_queue):

# After
def mock_execute(conn, scope, cancel_event, log_queue, doc_root=".", run_id=None):
```

---

## 実装順序（TDD）

1. **Phase 1** (Red → Green → Commit)
   - テスト追加 → 失敗確認
   - executor.py修正 → テストパス
   - コミット

2. **Phase 2** (Red → Green → Commit)
   - テスト追加 → 失敗確認
   - executor.py, manager.py, runs.py修正 → テストパス
   - コミット

3. **Phase 3** (Red → Green → Commit)
   - テスト追加 → 失敗確認
   - dependencies.py修正 → テストパス
   - コミット

4. **Phase 4** (Commit)
   - テストモック修正
   - 全テストパス確認
   - コミット

---

## 検証

```bash
# 全テストパス
uv run pytest

# 静的解析パス
uv run pyright
```

## Critical Files

1. `src/genglossary/runs/executor.py`
2. `src/genglossary/runs/manager.py`
3. `src/genglossary/api/routers/runs.py`
4. `src/genglossary/api/dependencies.py`
5. `tests/runs/test_manager.py`
6. `tests/runs/test_executor.py`
7. `tests/api/test_dependencies.py`（新規）
