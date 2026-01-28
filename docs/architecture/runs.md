# Run管理 (Schema v3)

**役割**: バックグラウンドでのパイプライン実行管理とステータス追跡

GUIアプリケーションから非同期にパイプラインを実行するための管理システム。各プロジェクトで1つのアクティブRunのみを許可し、進捗ログをストリーミングで提供します。

## スキーマ (Schema v3)

```sql
CREATE TABLE runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scope TEXT NOT NULL,  -- 'full' | 'from_terms' | 'provisional_to_refined'
    status TEXT NOT NULL, -- 'pending' | 'running' | 'completed' | 'cancelled' | 'failed'
    started_at TEXT,
    finished_at TEXT,
    triggered_by TEXT NOT NULL DEFAULT 'api',
    error_message TEXT,
    progress_current INTEGER,
    progress_total INTEGER,
    current_step TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

## runs_repository.py (Runs CRUD)

```python
def create_run(
    conn: sqlite3.Connection,
    scope: str,
    triggered_by: str = "api"
) -> int:
    """新しいRunレコードを作成（status='pending'）"""
    ...

def get_run(conn: sqlite3.Connection, run_id: int) -> sqlite3.Row | None:
    """Run詳細を取得"""
    ...

def get_active_run(conn: sqlite3.Connection) -> sqlite3.Row | None:
    """アクティブなRun（pending or running）を取得"""
    cursor.execute(
        "SELECT * FROM runs WHERE status IN ('pending', 'running') ORDER BY id DESC LIMIT 1"
    )
    ...

def list_runs(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """全Run履歴を取得（created_at降順）"""
    ...

def update_run_status(
    conn: sqlite3.Connection,
    run_id: int,
    status: str,
    started_at: datetime | None = None,
    finished_at: datetime | None = None,
    error_message: str | None = None
) -> None:
    """Runステータスを更新"""
    ...

def cancel_run(conn: sqlite3.Connection, run_id: int) -> None:
    """Runをキャンセル（status='cancelled', finished_at設定）"""
    ...
```

## manager.py (RunManager - スレッド管理)

```python
from threading import Event, Thread
from queue import Queue

class RunManager:
    """パイプラインのバックグラウンド実行を管理

    プロジェクトごとに1つのアクティブRunのみを許可し、
    ログストリーミングを提供します。
    """

    def __init__(self, db_path: str):
        """RunManagerを初期化

        Args:
            db_path: プロジェクトDBのパス（Connection ではなくパス）

        Note:
            各スレッドが独自の接続を作成することで、SQLiteの
            threading制限とSegmentation Faultを回避します。
        """
        self.db_path = db_path
        self._thread: Thread | None = None
        self._cancel_event = Event()
        self._log_queue: Queue = Queue()

    def start_run(self, scope: str) -> int:
        """バックグラウンドでRunを開始

        Returns:
            作成されたRunのID

        Raises:
            RuntimeError: 既にRunが実行中の場合
        """
        # 接続を作成してアクティブRunをチェック
        conn = get_connection(self.db_path)
        try:
            active_run = get_active_run(conn)
            if active_run is not None:
                raise RuntimeError(f"Run already running: {active_run['id']}")

            run_id = create_run(conn, scope=scope)
        finally:
            conn.close()

        # バックグラウンドスレッドを起動
        self._thread = Thread(target=self._execute_run, args=(run_id, scope))
        self._thread.daemon = True
        self._thread.start()

        return run_id

    def _execute_run(self, run_id: int, scope: str) -> None:
        """バックグラウンドスレッドでRunを実行

        Note:
            このメソッドは別スレッドで実行されるため、
            独自のDB接続を作成します。
        """
        # スレッド内で新しい接続を作成
        conn = get_connection(self.db_path)

        try:
            update_run_status(conn, run_id, "running", started_at=datetime.now())

            # パイプライン実行
            executor = PipelineExecutor()
            executor.execute(conn, scope, self._cancel_event, self._log_queue)

            if self._cancel_event.is_set():
                cancel_run(conn, run_id)
            else:
                update_run_status(conn, run_id, "completed", finished_at=datetime.now())

        except Exception as e:
            update_run_status(conn, run_id, "failed", finished_at=datetime.now(), error_message=str(e))
        finally:
            # スレッド終了時に接続を閉じる
            conn.close()
```

## SQLite スレッディング戦略

1. **API層**: リクエストごとに接続を作成・破棄（`get_project_db()` dependency）
2. **RunManager**: `db_path` を保持し、各スレッドで独自の接続を作成
3. **check_same_thread=False**: FastAPI非同期処理とバックグラウンドスレッド対応

これにより、以下の問題を解決:
- APIリクエスト終了時の接続クローズとバックグラウンドスレッドの競合を回避
- Segmentation Fault防止
- プロジェクト間の完全な隔離

## executor.py (PipelineExecutor - パイプライン実行)

```python
class PipelineExecutor:
    """用語集生成パイプラインステップを実行

    CLIのパイプラインコンポーネント（DocumentLoader, TermExtractor等）を
    再利用し、キャンセルと進捗レポートをサポートします。
    """

    def execute(
        self,
        conn: sqlite3.Connection,
        scope: str,
        cancel_event: Event,
        log_queue: Queue,
    ) -> None:
        """指定されたスコープでパイプラインを実行

        Args:
            conn: プロジェクトDB接続（スレッド内で作成されたもの）
            scope: 実行スコープ
            cancel_event: キャンセルシグナル
            log_queue: ログメッセージキュー
        """
        if scope == "full":
            self._execute_full(conn, cancel_event, log_queue)
        elif scope == "from_terms":
            self._execute_from_terms(conn, cancel_event, log_queue)
        elif scope == "provisional_to_refined":
            self._execute_provisional_to_refined(conn, cancel_event, log_queue)
```

## 実行スコープ

| Scope | 実行ステップ | 用途 |
|-------|------------|------|
| `full` | 1→2→3→4→5 | 全パイプライン実行（ドキュメント読み込みから） |
| `from_terms` | 3→4→5 | 既存の抽出用語から用語集生成 |
| `provisional_to_refined` | 4→5 | 既存の暫定用語集から精査・改善 |

**パイプラインステップ:**
1. ドキュメント読み込み (DocumentLoader / DBから直接読み込み)
2. 用語抽出 (TermExtractor)
3. 用語集生成 (GlossaryGenerator)
4. 精査 (GlossaryReviewer)
5. 改善 (GlossaryRefiner)

**ドキュメント読み込みの方式 (Schema v4):**
- `full` スコープ: DocumentLoaderでファイルシステムから読み込み後、file_name + content をDBに保存
- `from_terms` / `provisional_to_refined`: DBから直接contentを取得（`_load_documents_from_db()`）
- GUIからのファイル追加: HTML5 File APIでブラウザから読み取り、APIを通じてDBに保存

各ステップで:
- キャンセルイベントをチェック
- 進捗メッセージを `log_queue` に送信
- 中間結果をDBに保存

## スレッディングアーキテクチャ

```
┌─────────────────────────────────────────────┐
│ FastAPI (Uvicorn Worker - Main Thread)     │
│                                             │
│  POST /api/projects/1/runs                  │
│    ↓                                        │
│  get_run_manager(db_path) ← dependency      │
│    ↓                                        │
│  RunManager(db_path)                        │
│    ↓                                        │
│  start_run(scope="full")                    │
│    ├─ Connection作成（短命）                │
│    ├─ create_run(conn, "full")              │
│    ├─ Connection閉じる                      │
│    └─ Thread.start() ────────────────────┐  │
│                                          │  │
│  Response返却 (Run ID)                   │  │
└──────────────────────────────────────────┼──┘
                                           │
┌──────────────────────────────────────────┼──┐
│ Background Thread                        │  │
│                                          ↓  │
│  _execute_run(run_id, scope):               │
│    ├─ Connection作成（スレッド専用）        │
│    ├─ update_run_status(conn, "running")    │
│    ├─ PipelineExecutor.execute(conn, ...)   │
│    │    ├─ DocumentLoader                    │
│    │    ├─ TermExtractor                     │
│    │    ├─ GlossaryGenerator                 │
│    │    ├─ GlossaryReviewer                  │
│    │    └─ GlossaryRefiner                   │
│    ├─ update_run_status(conn, "completed")   │
│    └─ Connection閉じる                       │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ GET /api/projects/1/runs/123/logs (SSE)    │
│                                             │
│  event_generator():                         │
│    while True:                              │
│      log_msg = log_queue.get(timeout=1)     │
│      yield f"data: {json.dumps(log_msg)}"   │
└─────────────────────────────────────────────┘
```

**重要なポイント:**

1. **接続の独立性**: メインスレッドとバックグラウンドスレッドは別々の接続を使用
2. **ライフサイクル**: 各接続は使用後すぐに閉じられる（finally block）
3. **キャンセル処理**: `Event` を使用してスレッド間でキャンセルをシグナル
4. **ログストリーミング**: `Queue` 経由でSSE（Server-Sent Events）形式で配信

## Runs API実装詳細

### run_schemas.py
```python
class RunStartRequest(BaseModel):
    """Run開始リクエスト"""
    scope: str = Field(..., description="Execution scope")

class RunResponse(BaseModel):
    """Run情報レスポンス"""
    id: int
    scope: str
    status: str
    started_at: datetime | None
    finished_at: datetime | None
    triggered_by: str
    error_message: str | None

    @classmethod
    def from_db_row(cls, row: Any) -> "RunResponse":
        """DB行から変換"""
        ...
```

### runs.py (Runs Router)
```python
router = APIRouter(prefix="/api/projects/{project_id}/runs", tags=["runs"])

def get_run_manager(db_path: str = Depends(get_project_db_path)) -> RunManager:
    """RunManagerインスタンスを取得（db_path dependency使用）"""
    return RunManager(db_path)

@router.post("", response_model=RunResponse, status_code=201)
async def start_run(
    request: RunStartRequest,
    manager: RunManager = Depends(get_run_manager),
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> RunResponse:
    """新しいRunを開始（409 if already running）"""
    ...

@router.get("/{run_id}/logs")
async def stream_run_logs(
    run_id: int,
    manager: RunManager = Depends(get_run_manager),
) -> StreamingResponse:
    """SSEでログをストリーミング"""
    async def event_generator():
        log_queue = manager.get_log_queue()
        while True:
            log_msg = log_queue.get(timeout=1)
            if log_msg is None:  # Sentinel値
                yield "event: complete\ndata: {}\n\n"
                break
            yield f"data: {json.dumps(log_msg)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
```

### dependencies.py (db_path dependency)
```python
def get_project_db_path(project: Project = Depends(get_project_by_id)) -> str:
    """プロジェクトDBパスを取得

    RunManager用の依存性。接続ではなくパスを返すことで、
    各スレッドが独自の接続を作成できるようにします。
    """
    return project.db_path
```

## 依存性注入の階層（Runs API専用）

```
get_registry_db()
    ↓ Depends
get_project_by_id(registry_conn)
    ↓ Depends
get_project_db_path(project) → str
    ↓ Depends
get_run_manager(db_path) → RunManager
```

通常のAPI（Terms, Provisional等）は `get_project_db()` を使用して接続を受け取りますが、RunManagerは`get_project_db_path()` でパスを受け取り、スレッド内で独自の接続を作成します。

## テスト構成

**tests/db/test_runs_repository.py (20 tests)**
- CRUD操作、ステータス遷移、プロジェクト隔離

**tests/runs/test_manager.py (13 tests)**
- start_run, cancel_run, スレッド起動、ログキャプチャ

**tests/runs/test_executor.py (10 tests)**
- Full/From-Terms/Provisional-to-Refined scopeの実行
- キャンセル処理
- 進捗ログ
- DBからのドキュメント読み込み（v4対応）

**tests/api/routers/test_runs.py (10 tests)**
- API統合テスト（POST/DELETE/GET エンドポイント）

**合計: 53 tests** (Repository 20 + Manager 13 + Executor 10 + API 10)
