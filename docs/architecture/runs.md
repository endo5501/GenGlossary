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

def complete_run_if_not_cancelled(conn: sqlite3.Connection, run_id: int) -> bool:
    """Runを原子的に完了（キャンセル済みまたは終了済みでなければ）

    レースコンディション防止: キャンセルチェックとステータス更新の間に
    別スレッドからキャンセルされても、completedに上書きしない。

    Returns:
        bool: completedに更新できればTrue、既に終了状態ならFalse
    """
    ...
```

## manager.py (RunManager - スレッド管理)

```python
from threading import Event, Lock, Thread
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
        self._cancel_events: dict[int, Event] = {}  # Per-run cancellation
        self._cancel_events_lock = Lock()
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

        # Create cancel event for this run
        cancel_event = Event()
        with self._cancel_events_lock:
            self._cancel_events[run_id] = cancel_event

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
            接続作成が失敗した場合もクリーンアップと完了シグナルを保証します。
        """
        conn = None
        try:
            # スレッド内で新しい接続を作成
            conn = get_connection(self.db_path)

            update_run_status(conn, run_id, "running", started_at=datetime.now())

            # Get cancel event (guaranteed to exist, created in start_run)
            with self._cancel_events_lock:
                cancel_event = self._cancel_events[run_id]

            # 実行コンテキストを作成
            context = ExecutionContext(
                run_id=run_id,
                log_callback=lambda msg: self._broadcast_log(run_id, msg),
                cancel_event=cancel_event,
            )

            # パイプライン実行
            executor = PipelineExecutor()
            executor.execute(conn, scope, context, doc_root=self.doc_root)

            # Race condition safe: complete_run_if_not_cancelled prevents
            # completing a run that was cancelled between is_set() and update
            if cancel_event.is_set():
                cancel_run(conn, run_id)
            else:
                complete_run_if_not_cancelled(conn, run_id)

        except Exception as e:
            # フルトレースバックをキャプチャしてデバッグ容易化
            error_message = str(e)
            error_traceback = traceback.format_exc()
            # ヘルパーメソッドで堅牢なステータス更新
            self._update_failed_status(conn, run_id, error_message)
            self._broadcast_log(run_id, {
                "run_id": run_id, "level": "error",
                "message": ..., "traceback": error_traceback
            })
        finally:
            # Cleanup cancel event for this run
            with self._cancel_events_lock:
                self._cancel_events.pop(run_id, None)
            # 完了シグナルを送信
            self._broadcast_log(run_id, {"run_id": run_id, "complete": True})
            # スレッド終了時に接続を閉じる（接続があれば）
            if conn is not None:
                conn.close()

    def _try_update_status(self, conn, run_id, error_message) -> bool:
        """ステータス更新を試行し、成功時にTrueを返す

        失敗時はwarningログをブロードキャストして False を返す。
        """
        ...

    def _update_failed_status(self, conn, run_id, error_message) -> None:
        """フォールバック接続付きでステータスを 'failed' に更新

        1. 既存の conn でステータス更新を試行
        2. 失敗した場合、新しい接続を作成してフォールバック
        3. フォールバックも失敗した場合、warningログを出力

        Note:
            両方の接続が失敗しても、エラーログのブロードキャストは保証される。
        """
        if conn is not None and self._try_update_status(conn, run_id, error_message):
            return

        try:
            with database_connection(self.db_path) as fallback_conn:
                self._try_update_status(fallback_conn, run_id, error_message)
        except Exception as e:
            self._broadcast_log(run_id, {"level": "warning", "message": f"Failed to create fallback connection: {e}"})
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

### PipelineScope Enum

実行スコープを定義する列挙型。マジックストリングを排除し、型安全性を向上。

```python
class PipelineScope(Enum):
    """パイプライン実行スコープの列挙型"""
    FULL = "full"                                    # 全ステップ実行
    FROM_TERMS = "from_terms"                        # 用語抽出済みから再開
    PROVISIONAL_TO_REFINED = "provisional_to_refined" # 暫定用語集から精査
```

### ExecutionContext (スレッドセーフティ)

実行固有の状態をカプセル化するイミュータブルなdataclass。各実行が独立した状態を持つことを保証し、同一の `PipelineExecutor` インスタンスで並行実行可能にします。

```python
@dataclass(frozen=True)
class ExecutionContext:
    """実行コンテキスト（スレッドセーフ）

    各実行の状態を明示的に管理:
    - run_id: ログフィルタリング用の実行ID
    - log_callback: ログメッセージ送信用コールバック
    - cancel_event: キャンセルシグナル
    """
    run_id: int
    log_callback: Callable[[dict], None]
    cancel_event: Event
```

### PipelineExecutor クラス

```python
class PipelineExecutor:
    """用語集生成パイプラインステップを実行

    CLIのパイプラインコンポーネント（DocumentLoader, TermExtractor等）を
    再利用し、キャンセルと進捗レポートをサポートします。

    Thread Safety:
        ExecutionContext を使用することで、LLMクライアントを共有しつつ
        各実行の状態（run_id, log_callback, cancel_event）を分離します。
    """

    def execute(
        self,
        conn: sqlite3.Connection,
        scope: str | PipelineScope,  # Enum または文字列を受け付け
        context: ExecutionContext,   # 実行コンテキスト
        doc_root: str = ".",
    ) -> None:
        """指定されたスコープでパイプラインを実行

        Args:
            conn: プロジェクトDB接続（スレッド内で作成されたもの）
            scope: 実行スコープ（PipelineScope または文字列）
            context: 実行コンテキスト（run_id, log_callback, cancel_event）
            doc_root: ドキュメントルートディレクトリ

        Raises:
            ValueError: 不明なスコープが指定された場合
        """
        # Enum を文字列値に変換
        scope_value = scope.value if isinstance(scope, PipelineScope) else scope

        if scope_value == PipelineScope.FULL.value:
            self._execute_full(conn, context, doc_root)
        elif scope_value == PipelineScope.FROM_TERMS.value:
            self._execute_from_terms(conn, context)
        elif scope_value == PipelineScope.PROVISIONAL_TO_REFINED.value:
            self._execute_provisional_to_refined(conn, context)
        else:
            raise ValueError(f"Unknown scope: {scope_value}")
```

### 進捗コールバック

用語集生成・精査ステップでは、各用語の処理進捗をリアルタイムでログストリームに送信します。

```python
# types.py
TermProgressCallback = Callable[[int, int, str], None]  # (current, total, term_name)

# executor.py
def _create_progress_callback(
    self,
    context: ExecutionContext,  # コンテキストを使用
    step_name: str,
) -> Callable[[int, int, str], None]:
    """進捗コールバックを生成。ログに拡張フィールドを含める。"""
    def callback(current: int, total: int, term_name: str = "") -> None:
        percent = int((current / total) * 100) if total > 0 else 0
        self._log(
            context,  # コンテキスト経由でログ
            "info",
            f"{term_name}: {percent}%",
            step=step_name,
            current=current,
            total=total,
            current_term=term_name,
        )
    return callback
```

**拡張ログメッセージフォーマット:**
```json
{
    "run_id": 1,
    "level": "info",
    "message": "量子コンピュータ: 25%",
    "step": "provisional",
    "progress_current": 5,
    "progress_total": 20,
    "current_term": "量子コンピュータ"
}
```

**GlossaryGenerator / GlossaryRefiner での使用:**
```python
# executor.py
progress_cb = self._create_progress_callback(conn, "provisional")
glossary = generator.generate(
    extracted_terms, documents, term_progress_callback=progress_cb
)
```

## 実行スコープ

| Scope | 実行ステップ | 用途 |
|-------|------------|------|
| `full` | 1→2→3→4→5 | 全パイプライン実行（ドキュメント読み込みから） |
| `from_terms` | 3→4→5 | 既存の抽出用語から用語集生成 |
| `provisional_to_refined` | 4→5 | 既存の暫定用語集から精査・改善 |

**重複用語の処理:**
- 用語抽出ステップ（ステップ2）で LLM が同じ用語を複数回返した場合、重複はスキップされ、ユニークな用語のみが DB に保存されます

**issues がない場合の動作:**
- GlossaryReviewer が問題点を検出しなかった場合（`issues == []`）、GlossaryRefiner は呼び出されません
- 代わりに、provisional glossary がそのまま refined glossary としてコピー保存されます

**パイプラインステップ:**
1. ドキュメント読み込み (DocumentLoader / DBから直接読み込み)
2. 用語抽出 (TermExtractor)
3. 用語集生成 (GlossaryGenerator)
4. 精査 (GlossaryReviewer)
5. 改善 (GlossaryRefiner)

**ドキュメント読み込みの方式 (Schema v4 - DB-first approach):**

`_load_documents()` メソッドがDB優先アプローチでドキュメントを読み込みます：

```
1. まずDBからドキュメントを読み込み
   ↓ DBにドキュメントがあれば
   → そのまま使用（GUIモード）

   ↓ DBが空で doc_root が指定されていれば
   → ファイルシステムから読み込み、DBに保存（CLIモード）

   ↓ 両方とも空なら
   → RuntimeError("Cannot execute pipeline without documents")
```

| 条件 | 動作 |
|------|------|
| DBにドキュメントあり | DBから読み込み（GUIモード） |
| DBが空 + `doc_root` 指定あり | ファイルシステムから読み込み、DBに保存（CLIモード） |
| DBが空 + `doc_root` 未指定/`"."` | エラー |

**ファイル名の保存:**
- CLIモードでファイルシステムから読み込む場合、`file_name` には `doc_root` からの相対パスが保存されます
  - 例: `doc_root=/project/docs` で `/project/docs/chapter1/intro.md` を読み込むと、`file_name` は `chapter1/intro.md`
- これにより:
  - 異なるディレクトリにある同名ファイル（例: `docs/README.md` と `examples/README.md`）の衝突を回避
  - サーバーの絶対パス漏洩を防止（セキュリティ）
  - DBの環境間移動時の互換性を向上（ポータビリティ）

- `full` / `from_terms` / `provisional_to_refined`: すべて `_load_documents()` を使用
- GUIからのファイル追加: HTML5 File APIでブラウザから読み取り、APIを通じてDBに保存

**DB-firstアプローチの理由:**
- GUIプロジェクト作成時に `doc_root` が自動生成されるが、ドキュメントはDBに保存される
- `doc_root` の値だけではGUI/CLIモードを判定できないため、DBの有無で判断
- CLI: DBが空の場合のみファイルシステムにフォールバック

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

**tests/db/test_runs_repository.py (25 tests)**
- CRUD操作、ステータス遷移、プロジェクト隔離
- complete_run_if_not_cancelled（レースコンディション防止）

**tests/runs/test_manager.py (40 tests)**
- start_run, cancel_run, スレッド起動、ログキャプチャ
- per-run cancellation（各runに個別のキャンセルイベント）
- cancellation race condition（キャンセルとステータス更新の競合防止）
- connection error handling（接続エラー時のクリーンアップとフォールバック）
- warning log broadcast（ステータス更新失敗時の警告ログ）

**tests/runs/test_executor.py (43 tests)**
- Full/From-Terms/Provisional-to-Refined scopeの実行
- キャンセル処理
- 進捗ログ
- DB-first document loading（v4対応）
  - GUIモード: DBにドキュメントがあればDBから読み込み
  - CLIモード: DBが空なら `doc_root` から読み込み
  - 両方空ならエラー
- バグ修正テスト
  - issues なしでの refined 保存
  - 重複用語のスキップ
  - 同名ファイルの衝突回避
- ExecutionContext とスレッドセーフティテスト
  - コンテキスト経由の状態管理
  - 並行実行時の状態分離
  - 不明スコープのエラー処理

**tests/api/routers/test_runs.py (10 tests)**
- API統合テスト（POST/DELETE/GET エンドポイント）

**合計: 118 tests** (Repository 25 + Manager 40 + Executor 43 + API 10)
