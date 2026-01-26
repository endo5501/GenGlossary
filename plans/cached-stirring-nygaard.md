# Code Simplification Refactoring Plan

## 概要

code-simplifierエージェントのレビュー結果に基づき、高優先度＋中優先度の改善を実施する。

## 対象ファイル

| ファイル | 改善内容 | 優先度 |
|---------|---------|--------|
| `src/genglossary/runs/manager.py` | 未使用コード削除 + ヘルパー抽出 | 高 |
| `tests/runs/test_manager.py` | 不要テスト削除 | 高 |
| `src/genglossary/api/dependencies.py` | 早期リターンリファクタリング | 高 |
| `src/genglossary/api/routers/runs.py` | 完了チェックロジック統一 | 中 |

---

## 改善項目

### 1. RunManager: 未使用コード削除 [高]

**対象**: `src/genglossary/runs/manager.py`

**削除対象**:
- 行51: `self._log_queue: Queue = Queue(maxsize=self.MAX_LOG_QUEUE_SIZE)`
- 行253-259: `get_log_queue()`メソッド全体

**理由**: `_log_queue`は定義されているが、本番コードで使用されていない。`get_log_queue()`はテストでのみ使用。

**テスト修正**: `tests/runs/test_manager.py`
- 行301-303: `test_get_log_queue_returns_queue`テストを削除

---

### 2. RunManager: _broadcast_logのヘルパー抽出 [高]

**対象**: `src/genglossary/runs/manager.py` 行226-251

**現在のコード** (行236-250):
```python
for queue in self._subscribers[run_id]:
    if message.get("complete"):
        while True:
            try:
                queue.put_nowait(message)
                break
            except Full:
                try:
                    queue.get_nowait()
                except Empty:
                    continue
    else:
        try:
            queue.put_nowait(message)
        except Full:
            pass
```

**リファクタリング後**:
```python
def _put_to_queue(self, queue: Queue, message: dict) -> None:
    """Put message to queue, ensuring completion signals are delivered."""
    if message.get("complete"):
        # For completion signals, make space if needed
        while queue.full():
            try:
                queue.get_nowait()
            except Empty:
                break
    try:
        queue.put_nowait(message)
    except Full:
        pass  # Only regular messages are dropped when full
```

**_broadcast_log内での使用**:
```python
for queue in self._subscribers[run_id]:
    self._put_to_queue(queue, message)
```

---

### 3. Dependencies: 早期リターンリファクタリング [高]

**対象**: `src/genglossary/api/dependencies.py` 行111-146

**現在のコード**:
```python
def get_run_manager(project: Project = Depends(get_project_by_id)) -> RunManager:
    with _registry_lock:
        existing = _run_manager_registry.get(project.db_path)
        if existing is not None:
            settings_match = (
                existing.doc_root == project.doc_root
                and existing.llm_provider == project.llm_provider
                and existing.llm_model == project.llm_model
            )
            if settings_match or existing.get_active_run() is not None:
                return existing
        manager = RunManager(...)
        _run_manager_registry[project.db_path] = manager
        return manager
```

**リファクタリング後**:
```python
def _settings_match(manager: RunManager, project: Project) -> bool:
    """Check if manager settings match project settings."""
    return (
        manager.doc_root == project.doc_root
        and manager.llm_provider == project.llm_provider
        and manager.llm_model == project.llm_model
    )

def _create_and_register_manager(project: Project) -> RunManager:
    """Create and register a new RunManager."""
    manager = RunManager(
        db_path=project.db_path,
        doc_root=project.doc_root,
        llm_provider=project.llm_provider,
        llm_model=project.llm_model,
    )
    _run_manager_registry[project.db_path] = manager
    return manager

def get_run_manager(project: Project = Depends(get_project_by_id)) -> RunManager:
    """Get or create RunManager instance for the project."""
    with _registry_lock:
        existing = _run_manager_registry.get(project.db_path)

        if existing is None:
            return _create_and_register_manager(project)

        if existing.get_active_run() is not None:
            return existing

        if _settings_match(existing, project):
            return existing

        return _create_and_register_manager(project)
```

---

### 4. Runs API: 完了チェックロジック統一 [中]

**対象**: `src/genglossary/api/routers/runs.py`

**現在の重複** (行181, 200):
```python
{"completed", "failed", "cancelled"}  # 2箇所で同一セット
```

**リファクタリング**:
```python
# ファイル冒頭に定数定義
_FINISHED_STATUSES: set[str] = {"completed", "failed", "cancelled"}

# 関数内でヘルパー使用
def _is_run_finished(run_row: sqlite3.Row | None) -> bool:
    """Check if run is in a finished state."""
    return run_row is not None and run_row["status"] in _FINISHED_STATUSES
```

---

### 5. PipelineExecutor: キャンセルチェック [対象外]

**評価結果**: 現状維持が妥当
- 10箇所で呼び出されているが、各ステップ前のチェック意図が明確
- `if self._check_cancellation(): return` は読みやすい
- デコレータ化は例外フローを複雑化するリスクあり

---

## 実装手順

1. **テスト削除**: `test_get_log_queue_returns_queue`を削除
2. **RunManager修正**: 未使用コード削除 + `_put_to_queue`ヘルパー追加
3. **Dependencies修正**: 早期リターン + ヘルパー関数抽出
4. **Runs API修正**: 完了ステータス定数化 + ヘルパー関数
5. **テスト実行**: 全テストがパスすることを確認
6. **コミット**: `Refactor code based on code-simplifier review`

---

## 検証方法

```bash
# 全テスト実行
uv run pytest

# 静的解析
uv run pyright src/genglossary/runs/manager.py src/genglossary/api/dependencies.py src/genglossary/api/routers/runs.py

# 変更ファイル確認
git diff --stat
```

**期待結果**:
- 650テスト全てパス
- pyright 0 errors
