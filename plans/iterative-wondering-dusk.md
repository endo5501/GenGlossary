# Log Streaming改善: Run単位Queue + Subscribe登録（Option A）

## 概要

SSEログストリーミングの問題を解決するため、Option Aを実装する。

### 解決する問題
1. **High**: `run_id`フィルタの再投入ループでビジーになり、keepaliveが送信されない
2. **Medium**: 単一Queue方式で複数SSEクライアント接続時にログが分配される

## TDDアプローチ

TDD（テスト駆動開発）で進める：
1. 先にテストを追加（Red）
2. テストが失敗することを確認
3. 実装を完了（Green）
4. リファクタリング

## 実装計画

### Phase 1: テスト追加（TDD Red）

**ファイル**: `tests/runs/test_manager.py`

新規テスト追加:
```python
class TestRunManagerSubscription:
    """Tests for RunManager subscription functionality."""

    def test_register_subscriber_creates_queue(self, manager: RunManager) -> None:
        """register_subscriberはQueueを作成して返す"""
        queue = manager.register_subscriber(run_id=1)
        assert queue is not None

    def test_multiple_subscribers_same_run_get_same_logs(self, manager: RunManager) -> None:
        """同じrunの複数subscriberが同じログを受信する"""
        queue1 = manager.register_subscriber(run_id=1)
        queue2 = manager.register_subscriber(run_id=1)

        manager._broadcast_log(1, {"level": "info", "message": "test"})

        log1 = queue1.get_nowait()
        log2 = queue2.get_nowait()
        assert log1 == log2

    def test_subscribers_only_receive_their_run_logs(self, manager: RunManager) -> None:
        """subscriberは自分のrunのログのみ受信する"""
        queue1 = manager.register_subscriber(run_id=1)
        queue2 = manager.register_subscriber(run_id=2)

        manager._broadcast_log(1, {"level": "info", "message": "run1"})

        log1 = queue1.get_nowait()
        assert log1["message"] == "run1"
        assert queue2.empty()

    def test_unregister_subscriber_stops_receiving(self, manager: RunManager) -> None:
        """unregister後はログを受信しない"""
        queue = manager.register_subscriber(run_id=1)
        manager.unregister_subscriber(run_id=1, queue=queue)

        manager._broadcast_log(1, {"level": "info", "message": "test"})

        assert queue.empty()
```

**ファイル**: `tests/runs/test_executor.py`

新規テスト追加:
```python
def test_executor_uses_log_callback(self) -> None:
    """executorがlog_callbackを使ってログを出力する"""
    logs = []
    callback = lambda msg: logs.append(msg)

    executor = PipelineExecutor()
    executor.execute(conn, "full", Event(), callback, doc_root=".", run_id=1)

    assert len(logs) > 0
    assert all(log.get("run_id") == 1 for log in logs)
```

### Phase 2: RunManagerの変更（TDD Green）

**ファイル**: `src/genglossary/runs/manager.py`

1. **インポート追加**:
```python
from threading import Event, Lock, Thread
from typing import Callable
```

2. **`__init__`の変更**:
```python
def __init__(self, ...):
    # 既存のコード...

    # 削除: self._log_queue: Queue = Queue(maxsize=self.MAX_LOG_QUEUE_SIZE)

    # 追加: Subscriber管理
    self._subscribers: dict[int, set[Queue]] = {}
    self._subscribers_lock = Lock()
```

3. **Subscribe/Unsubscribeメソッド追加**:
```python
def register_subscriber(self, run_id: int) -> Queue:
    """SSEクライアント用のQueueを作成し登録"""
    queue: Queue = Queue(maxsize=self.MAX_LOG_QUEUE_SIZE)
    with self._subscribers_lock:
        if run_id not in self._subscribers:
            self._subscribers[run_id] = set()
        self._subscribers[run_id].add(queue)
    return queue

def unregister_subscriber(self, run_id: int, queue: Queue) -> None:
    """SSEクライアントの登録解除"""
    with self._subscribers_lock:
        if run_id in self._subscribers:
            self._subscribers[run_id].discard(queue)
            if not self._subscribers[run_id]:
                del self._subscribers[run_id]

def _broadcast_log(self, run_id: int, message: dict) -> None:
    """全subscriberにログをブロードキャスト"""
    with self._subscribers_lock:
        if run_id in self._subscribers:
            for queue in self._subscribers[run_id]:
                try:
                    queue.put_nowait(message)
                except:
                    pass  # Queue満杯時は破棄
```

4. **`_execute_run`の変更**:
```python
def _execute_run(self, run_id: int, scope: str) -> None:
    # ...

    # ログコールバックを作成
    def log_callback(msg: dict) -> None:
        self._broadcast_log(run_id, msg)

    # PipelineExecutorを呼び出し
    executor.execute(
        conn,
        scope,
        self._cancel_event,
        log_callback,  # Queue → callback
        doc_root=self.doc_root,
        run_id=run_id,
    )

    # ...

    # finally:
    #   完了シグナルをブロードキャスト
    self._broadcast_log(run_id, {"run_id": run_id, "complete": True})
```

5. **`get_log_queue()`を削除**（不要）

### Phase 3: PipelineExecutorの変更

**ファイル**: `src/genglossary/runs/executor.py`

1. **型定義追加**:
```python
from typing import Callable
```

2. **`execute()`のシグネチャ変更**:
```python
def execute(
    self,
    conn: sqlite3.Connection,
    scope: str,
    cancel_event: Event,
    log_callback: Callable[[dict], None],  # Queue → callback
    doc_root: str = ".",
    run_id: int | None = None,
) -> None:
```

3. **`_log()`ヘルパーの変更**:
```python
def __init__(self, ...):
    # ...
    self._log_callback: Callable[[dict], None] | None = None

def _log(self, level: str, message: str) -> None:
    if self._log_callback is not None:
        self._log_callback({"run_id": self._run_id, "level": level, "message": message})

def execute(self, ...):
    self._log_callback = log_callback
    # ...
```

### Phase 4: API Routerの変更

**ファイル**: `src/genglossary/api/routers/runs.py`

1. **`stream_run_logs`の変更**:
```python
@router.get("/{run_id}/logs")
async def stream_run_logs(...) -> StreamingResponse:
    # ...

    async def event_generator() -> AsyncIterator[str]:
        """Generate SSE events from log queue."""
        queue = manager.register_subscriber(run_id)
        try:
            while True:
                try:
                    log_msg = queue.get(timeout=1)

                    # 完了シグナル
                    if log_msg.get("complete"):
                        yield "event: complete\ndata: {}\n\n"
                        break

                    # ログ送信
                    yield f"data: {json.dumps(log_msg)}\n\n"

                except Empty:
                    yield ": keepalive\n\n"
        finally:
            manager.unregister_subscriber(run_id, queue)

    # ...
```

2. **削除**: run_idフィルタ・再投入ロジック（188-196行）

### Phase 5: 既存テストの修正

**ファイル**: `tests/runs/test_manager.py`

既存テストで`get_log_queue()`を使用しているテストを修正:
- `test_logs_are_captured_during_execution`
- `test_cancel_run_stops_execution`
- `test_logs_include_run_id`
- `test_completion_signal_includes_run_id`
- `test_sse_receives_completion_signal`

→ モックで`log_callback`をキャプチャする方式に変更

## 修正対象ファイル

| ファイル | 変更内容 |
|---------|---------|
| `src/genglossary/runs/manager.py` | Subscribe管理、ブロードキャスト、`_log_queue`削除 |
| `src/genglossary/runs/executor.py` | `log_queue` → `log_callback` |
| `src/genglossary/api/routers/runs.py` | subscribe/unsubscribe使用、フィルタ削除 |
| `tests/runs/test_manager.py` | 新規テスト4個 + 既存テスト修正5個 |
| `tests/runs/test_executor.py` | 新規テスト1個 + 既存テスト修正 |

## 検証方法

1. テスト追加後、失敗することを確認: `uv run pytest tests/runs/ -v`
2. 実装後、全テスト通過: `uv run pytest`
3. 静的解析: `uv run pyright`
4. 手動テスト:
   - 複数ターミナルでSSE接続し、同じログが両方に表示されることを確認
   - 別runのログが混在しないことを確認
