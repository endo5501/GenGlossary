# Run管理 (Schema v3)

**役割**: バックグラウンドでのパイプライン実行管理とステータス追跡

GUIアプリケーションから非同期にパイプラインを実行するための管理システム。各プロジェクトで1つのアクティブRunのみを許可し、進捗ログをストリーミングで提供します。

## スキーマ (Schema v3)

```sql
CREATE TABLE runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scope TEXT NOT NULL,  -- 'full' | 'extract' | 'generate' | 'review' | 'refine'
    status TEXT NOT NULL, -- 'pending' | 'running' | 'completed' | 'cancelled' | 'failed'
    started_at TEXT,
    finished_at TEXT,
    triggered_by TEXT NOT NULL DEFAULT 'api',
    error_message TEXT,
    progress_current INTEGER,
    progress_total INTEGER,
    current_step TEXT,  -- 'extract', 'provisional', 'issues', 'refined'
    created_at TEXT NOT NULL  -- Set by Python, not SQLite default
);
```

## runs_repository.py (Runs CRUD)

### Status Constants

```python
VALID_STATUSES = {"pending", "running", "completed", "failed", "cancelled"}
TERMINAL_STATUSES = {"completed", "failed", "cancelled"}

def _validate_status(status: str, allowed: set[str] | None = None) -> None:
    """Validate status value.

    Args:
        status: Status value to validate.
        allowed: Set of allowed status values. Defaults to VALID_STATUSES.

    Raises:
        ValueError: If status is not in the allowed set.
    """
```

### RunUpdateResult Enum

```python
class RunUpdateResult(Enum):
    """Result of conditional status update operations.

    Used by update_run_status_if_active, update_run_status_if_running,
    complete_run_if_not_cancelled, fail_run_if_not_terminal, and cancel_run.

    This enum distinguishes between different outcomes when updating run status:
    - UPDATED: Run was successfully updated
    - NOT_FOUND: Run does not exist
    - ALREADY_TERMINAL: Run exists but is not in the expected state for the update
      (e.g., already in a terminal state, or not in 'running' state when required)
    """

    UPDATED = "updated"
    NOT_FOUND = "not_found"
    ALREADY_TERMINAL = "terminal"
```

この enum により、「run が存在しない」と「run が期待される状態にない」を明確に区別できます。全ての条件付きステータス更新関数が統一的にこの enum を返します。

### CRUD Functions

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
        "SELECT * FROM runs WHERE status IN ('pending', 'running') ORDER BY created_at DESC, id DESC LIMIT 1"
    )
    ...

def get_current_or_latest_run(conn: sqlite3.Connection) -> sqlite3.Row | None:
    """アクティブなRunがあれば返し、なければ最新のRunを返す

    /current エンドポイント用。パイプライン完了後も完了状態を取得可能にする。
    アクティブなRun（pending/running）がある場合はそれを優先。
    なければ、ステータスに関係なく最新のRunを返す。
    """
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
    """Runステータスを更新

    Status Validation:
        VALID_STATUSES のみ受け付ける。不正な値は ValueError を発生。

    Error Message Clearing:
        非 terminal status (pending/running) への遷移時、error_message を自動的に NULL にクリア。
        これにより、failed → running → completed の遷移で古いエラーメッセージが残らない。
    """
    ...

def update_run_status_if_active(
    conn: sqlite3.Connection,
    run_id: int,
    status: str,
    error_message: str | None = None,
    finished_at: datetime | None = None
) -> RunUpdateResult:
    """アクティブな状態（pending/running）のRunのみステータスを更新

    終了状態（completed, cancelled, failed）のRunは更新しない。
    cancel_run, fail_run_if_not_terminal の共通ロジックを統合した汎用関数。

    Status Validation:
        TERMINAL_STATUSES のみ受け付ける（completed, failed, cancelled）。
        pending や running は ValueError を発生。finished_at を自動設定するため、
        terminal status 以外は意味をなさない。

    Args:
        finished_at: 終了タイムスタンプ（省略時は現在のUTC時刻を使用）
                     timezone-aware datetime のみ受け付ける

    Returns:
        RunUpdateResult indicating the outcome:
        - UPDATED: Run was successfully updated
        - NOT_FOUND: Run does not exist
        - ALREADY_TERMINAL: Run exists but is already in terminal state
    """
    ...

def update_run_status_if_running(
    conn: sqlite3.Connection,
    run_id: int,
    status: str,
    finished_at: datetime | None = None
) -> RunUpdateResult:
    """running状態のRunのみステータスを更新

    update_run_status_if_active とは異なり、pending状態のRunは更新しない。
    これにより、開始されていないRunが直接completedに遷移することを防ぐ。

    Status Validation:
        TERMINAL_STATUSES のみ受け付ける（completed, failed, cancelled）。
        update_run_status_if_active と一貫性を保つ。

    Args:
        finished_at: 終了タイムスタンプ（省略時は現在のUTC時刻を使用）
                     timezone-aware datetime のみ受け付ける

    Returns:
        RunUpdateResult indicating the outcome:
        - UPDATED: Run was successfully updated
        - NOT_FOUND: Run does not exist
        - ALREADY_TERMINAL: Run exists but is not in 'running' state
    """
    ...

def cancel_run(conn: sqlite3.Connection, run_id: int) -> RunUpdateResult:
    """Runをキャンセル（status='cancelled', finished_at設定）

    update_run_status_if_active の薄いラッパー。
    pending/running どちらからもキャンセル可能。

    Returns:
        RunUpdateResult indicating the outcome.
    """
    return update_run_status_if_active(conn, run_id, "cancelled")

def complete_run_if_not_cancelled(
    conn: sqlite3.Connection, run_id: int
) -> RunUpdateResult:
    """Runを原子的に完了（running状態の場合のみ）

    update_run_status_if_running の薄いラッパー。
    レースコンディション防止: 別スレッドからキャンセルされても上書きしない。

    Note:
        pending状態のRunは完了できない。必ず先にrunning状態に
        遷移してから完了する必要がある（started_atが設定される）。

    Returns:
        RunUpdateResult indicating the outcome:
        - UPDATED: Run was successfully completed
        - NOT_FOUND: Run does not exist
        - ALREADY_TERMINAL: Run exists but is not in 'running' state
    """
    return update_run_status_if_running(conn, run_id, "completed")

def fail_run_if_not_terminal(
    conn: sqlite3.Connection, run_id: int, error_message: str
) -> RunUpdateResult:
    """Runを原子的にfailedに更新（終了状態でなければ）

    update_run_status_if_active の薄いラッパー。
    pending/running どちらからもfailed遷移可能。
    終了状態（completed, cancelled, failed）のrunは上書きしない。

    Returns:
        RunUpdateResult indicating the outcome:
        - UPDATED: Run was successfully failed
        - NOT_FOUND: Run does not exist
        - ALREADY_TERMINAL: Run is already in a terminal state
    """
    return update_run_status_if_active(conn, run_id, "failed", error_message)
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

    def __init__(
        self,
        db_path: str,
        doc_root: str = ".",
        llm_provider: str = "ollama",
        llm_model: str = "",
        llm_base_url: str = "",
    ):
        """RunManagerを初期化

        Args:
            db_path: プロジェクトDBのパス（Connection ではなくパス）
            doc_root: ドキュメントのルートディレクトリ
            llm_provider: LLMプロバイダ名（"ollama" または "openai"）
            llm_model: LLMモデル名
            llm_base_url: LLM APIのベースURL

        Note:
            各スレッドが独自の接続を作成することで、SQLiteの
            threading制限とSegmentation Faultを回避します。
        """
        self.db_path = db_path
        self.doc_root = doc_root
        self.llm_provider = llm_provider
        self.llm_model = llm_model
        self.llm_base_url = llm_base_url
        self._thread: Thread | None = None
        self._cancel_events: dict[int, Event] = {}  # Per-run cancellation
        self._cancel_events_lock = Lock()
        self._start_run_lock = Lock()  # Synchronize start_run calls
        self._log_queue: Queue = Queue()
        self._completed_runs: dict[int, dict] = {}  # Track completed runs for late subscribers

    def start_run(self, scope: str, triggered_by: str = "api") -> int:
        """バックグラウンドでRunを開始

        Args:
            scope: 実行スコープ（"full", "extract", "generate", "review", "refine"）
            triggered_by: トリガー元（"api", "manual", "auto"）

        Returns:
            作成されたRunのID

        Raises:
            RuntimeError: 既にRunが実行中の場合

        Lock ordering: _start_run_lock -> database connection -> _cancel_events_lock
        この順序により、以下のレースコンディションを防止:
        - 並行する start_run 呼び出し
        - start_run と cancel_run の競合
        """
        # Synchronize to prevent race conditions between concurrent start_run calls
        with self._start_run_lock:
            # Check if a run is already active and create run record atomically
            with database_connection(self.db_path) as conn:
                active_run = get_active_run(conn)
                if active_run is not None:
                    raise RuntimeError(f"Run already running: {active_run['id']}")

                # Create run record atomically within the same lock
                with transaction(conn):
                    run_id = create_run(conn, scope=scope)

            # Create cancel event within the same lock to ensure consistency
            # DB状態とインメモリ状態の整合性を保証
            cancel_event = Event()
            with self._cancel_events_lock:
                self._cancel_events[run_id] = cancel_event

        # バックグラウンドスレッドを起動（ロック外で）
        try:
            self._thread = Thread(target=self._execute_run, args=(run_id, scope))
            self._thread.daemon = True
            self._thread.start()
        except Exception:
            # Cleanup on thread start failure
            with self._cancel_events_lock:
                self._cancel_events.pop(run_id, None)

            # Reset thread reference (it was never started)
            self._thread = None

            # Try to update DB status, but don't mask the original exception
            try:
                with database_connection(self.db_path) as conn:
                    with transaction(conn):
                        update_run_status(
                            conn, run_id, "failed",
                            error_message="Failed to start execution thread",
                            finished_at=datetime.now(timezone.utc),
                        )
            except Exception as db_error:
                self._broadcast_log(run_id, {
                    "run_id": run_id,
                    "level": "warning",
                    "message": f"Failed to update run status: {db_error}",
                })

            # Send completion signal and cleanup subscribers
            self._cleanup_run_resources(run_id, db_status="failed", status_update_failed=True)

            raise

        return run_id

    def _execute_run(self, run_id: int, scope: str) -> None:
        """バックグラウンドスレッドでRunを実行

        Note:
            このメソッドは別スレッドで実行されるため、
            独自のDB接続を作成します。
            接続作成が失敗した場合もクリーンアップと完了シグナルを保証します。

        重要: パイプライン実行とステータス更新は分離されています。
            これにより、パイプラインが成功してもDB更新が失敗した場合に
            ステータスが誤って 'failed' になる問題を防止します。
        """
        conn = None
        pipeline_error = None
        pipeline_traceback = None
        try:
            # スレッド内で新しい接続を作成
            conn = get_connection(self.db_path)

            update_run_status(conn, run_id, "running", started_at=datetime.now(timezone.utc))

            # Get cancel event (guaranteed to exist, created in start_run)
            with self._cancel_events_lock:
                cancel_event = self._cancel_events[run_id]

            # 実行コンテキストを作成
            context = ExecutionContext(
                run_id=run_id,
                log_callback=lambda msg: self._broadcast_log(run_id, msg),
                cancel_event=cancel_event,
            )

            # パイプライン実行（分離されたtry/except）
            executor = PipelineExecutor()
            try:
                executor.execute(conn, scope, context, doc_root=self.doc_root)
            except Exception as e:
                pipeline_error = e
                pipeline_traceback = traceback.format_exc()

            # ステータス更新（パイプライン実行とは別に処理）
            self._finalize_run_status(
                conn, run_id, cancel_event, pipeline_error, pipeline_traceback
            )

        except Exception as e:
            # 接続エラーなど、パイプライン外のエラー
            error_message = str(e)
            error_traceback = traceback.format_exc()
            self._update_failed_status(conn, run_id, error_message)
            self._broadcast_log(run_id, {
                "run_id": run_id, "level": "error",
                "message": ..., "traceback": error_traceback
            })
        finally:
            # Cleanup run resources (cancel event, completion signal, subscribers)
            self._cleanup_run_resources(run_id, db_status=final_status, status_update_failed=status_update_failed)
            # スレッド終了時に接続を閉じる（接続があれば）
            if conn is not None:
                conn.close()

    def _finalize_run_status(self, conn, run_id, pipeline_error, pipeline_traceback) -> None:
        """パイプライン実行後のステータスを確定

        ステータス更新ロジックをパイプライン実行から分離することで、
        ステータス更新の失敗がステータスの誤分類を引き起こすのを防止。

        優先順位:
        1. PipelineCancelledException → cancelled
        2. その他の例外 → failed
        3. 例外なし → completed

        Args:
            pipeline_error: executor.execute() から catch された例外、または None

        Note:
            isinstance(pipeline_error, PipelineCancelledException) でキャンセルを判定。
            これにより、キャンセルと通常のエラーを明確に区別できます。

        ステータス更新失敗時はフォールバック接続でリトライ。
        """
        ...

    def _try_update_status(
        self,
        conn: sqlite3.Connection | None,
        run_id: int,
        status: str,
        error_message: str | None = None,
    ) -> bool:
        """フォールバック接続付きステータス更新メソッド

        update_run_status_if_active を使用し、プライマリ接続で失敗した場合は
        新しいフォールバック接続で再試行。conn=None の場合は直接フォールバック。

        以前の _try_status_with_fallback と _update_failed_status を統合。
        lambda式によるコールバックパターンを排除し、直接呼び出しに簡素化。

        Args:
            conn: プライマリDB接続（None可、例外時はフォールバック）
            status: 新しいステータス（'cancelled', 'completed', 'failed'）
            error_message: failedステータスの場合のエラーメッセージ

        Returns:
            True: 成功、no-op（既に終了状態）、または存在しない場合
            False: プライマリとフォールバック両方が例外で失敗した場合

        フォールバックの流れ:
            1. conn が有効 → プライマリ接続で試行
            2. プライマリで例外 → フォールバック接続で再試行
            3. conn が None → 直接フォールバック接続を使用
            4. フォールバックも例外 → warning ログを出力し False を返す
        """
        ...

    def _log_update_result(
        self, run_id: int, status: str, result: RunUpdateResult
    ) -> None:
        """ステータス更新結果がno-opの場合にログを出力

        RunUpdateResult を使用して、「存在しない」と「既に終了状態」を
        区別したログメッセージを出力。

        ログメッセージの区別:
            - NOT_FOUND: "run not found"
            - ALREADY_TERMINAL: "run was already in terminal state"
        """
        ...

    def _cleanup_run_resources(
        self,
        run_id: int,
        db_status: str | None = None,
        status_update_failed: bool = False,
    ) -> None:
        """Runのクリーンアップ処理を統合

        1. cancel_event を削除
        2. 完了シグナルをブロードキャスト（DB状態を含む）
        3. subscribers を削除
        4. 完了シグナルを _completed_runs に保存（遅延登録対応）

        完了シグナルフォーマット:
        - 成功時: {"run_id": 1, "complete": True, "db_status": "completed"}
        - 失敗時: {"run_id": 1, "complete": True, "db_status": "failed", "status_update_failed": True}

        Note:
            ブロードキャストと subscriber 削除は同じロック内で実行され、
            race condition（ブロードキャスト後に登録された subscriber が
            完了シグナルを受け取れずに削除される問題）を防止します。

            _completed_runs に保存することで、クリーンアップ後に登録した
            subscriber も即座に完了シグナルを受け取れます。
        """
        ...

```

## タイムスタンプ形式

すべてのタイムスタンプ（`created_at`, `started_at`, `finished_at`）は **UTC ISO 8601形式** で保存されます。

**形式**: `YYYY-MM-DDTHH:MM:SS+00:00`

**例**: `2026-02-01T00:15:30+00:00`

**実装**:
```python
from datetime import datetime, timezone

# タイムスタンプの設定
timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
# → "2026-02-01T00:15:30+00:00"
```

**使用箇所**:
- `create_run`: `created_at` を Python で設定
- `update_run_status`: `started_at`, `finished_at` パラメータ（timezone-aware datetime のみ受け付ける）
- `update_run_status_if_active`: `finished_at` パラメータ（省略時は現在のUTC時刻を自動設定）
- `update_run_status_if_running`: `finished_at` パラメータ（省略時は現在のUTC時刻を自動設定）

## 状態遷移の制約

| 遷移元 | → running | → completed | → cancelled | → failed |
|--------|-----------|-------------|-------------|----------|
| pending | ✅ 可能 | ❌ 不可 | ✅ 可能 | ✅ 可能 |
| running | - | ✅ 可能 | ✅ 可能 | ✅ 可能 |

**重要**: `pending` から `completed` への直接遷移は不可。必ず `running` を経由する必要がある。
これにより `started_at` が設定されていないRunが `completed` になることを防ぐ。

**関数とサポートする遷移元**:
| 関数 | pending | running |
|------|---------|---------|
| `update_run_status_if_active` | ✅ | ✅ |
| `update_run_status_if_running` | ❌ | ✅ |

**タイムゾーン検証**:
`update_run_status`、`update_run_status_if_active`、`update_run_status_if_running` は naive datetime を拒否し、`ValueError` を発生させます。

**ヘルパー関数**:
タイムスタンプ処理は以下のヘルパー関数で統一されています：

```python
def _to_iso_string(dt: datetime | None, param_name: str) -> str | None:
    """Convert timezone-aware datetime to ISO string.
    Returns None if dt is None.
    Raises ValueError if dt is naive.
    """

def _current_utc_iso() -> str:
    """Get current UTC time as ISO string."""
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
    FULL = "full"        # generate → review → refine（extractを除く）
    EXTRACT = "extract"  # 用語抽出のみ
    GENERATE = "generate" # 用語集生成のみ
    REVIEW = "review"    # レビューのみ
    REFINE = "refine"    # 改善のみ
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

### PipelineCancelledException

キャンセル時に raise される専用例外クラス。これにより、キャンセルと通常のエラーを明確に区別できます。

```python
class PipelineCancelledException(Exception):
    """Raised when pipeline execution is cancelled by user request."""
```

### キャンセルチェックデコレータ

`@_cancellable` デコレータは、DRY原則に従いキャンセルチェックパターンを統一します。

```python
def _cancellable(func: Callable) -> Callable:
    """メソッド実行前にキャンセルをチェックするデコレータ

    装飾されたメソッドは ExecutionContext を引数として受け取る必要があります。
    キャンセルが検出された場合、PipelineCancelledException を raise します。
    """
    @wraps(func)
    def wrapper(self: "PipelineExecutor", *args, **kwargs):
        # kwargs または位置引数から context を検索
        context = kwargs.get("context")
        if context is None:
            for arg in args:
                if isinstance(arg, ExecutionContext):
                    context = arg
                    break

        if context is not None:
            self._check_cancellation(context)  # Raises if cancelled
        return func(self, *args, **kwargs)
    return wrapper
```

**適用先:**
- `_execute_full`: フルパイプライン実行
- `_execute_extract`: 用語抽出のみ
- `_execute_generate`: 用語集生成のみ
- `_execute_review`: レビューのみ
- `_execute_refine`: 改善のみ

### user_notes の受け渡し

各スコープハンドラは `_build_user_notes_map()` で DB から `user_notes` を取得し、パイプラインステップに渡します。

```python
@staticmethod
def _build_user_notes_map(term_rows: list[sqlite3.Row]) -> dict[str, str]:
    """term_rowsからuser_notes_mapを構築（空のnotesは除外）"""
    ...
```

- `_execute_full`: `list_all_terms()` → `_build_user_notes_map()` → `_do_generate`/`_do_review`/`_do_refine`
- `_execute_generate`: `list_all_terms()` → `_build_user_notes_map()` → `_do_generate`
- `_execute_review`: `list_all_terms()` → `_build_user_notes_map()` → `_do_review`
- `_execute_refine`: `list_all_terms()` → `_build_user_notes_map()` → `_do_refine`
- `_execute_extract`: user_notes不要（Extract前にbackup、Extract後にrestore）

**残存する明示的チェック:**
LLM呼び出しや最終保存の前には、レスポンシブなキャンセルのため明示的チェックが残ります。

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

    def __init__(
        self,
        provider: str = "ollama",
        model: str = "",
        base_url: str | None = None,
        review_batch_size: int = 10,  # GlossaryReviewer のバッチサイズ
        llm_debug: bool = False,
        debug_dir: str | None = None,
    ):
        """Initialize the PipelineExecutor.

        Args:
            provider: LLMプロバイダ名（"ollama" または "openai"）
            model: LLMモデル名
            base_url: LLM APIのベースURL（省略時は環境設定値）
            review_batch_size: レビューステップでのバッチサイズ。
                大量の用語（50件以上）でのタイムアウトを防ぐため、
                この数ずつLLMに送信します。デフォルト20件。
            llm_debug: LLMデバッグログの有効化（デフォルト: False）
            debug_dir: デバッグログファイルの出力先ディレクトリ
        """
        ...

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
            PipelineCancelledException: キャンセルされた場合
            ValueError: 不明なスコープが指定された場合
        """
        # Enum に正規化（文字列の場合は変換）
        scope_enum = scope if isinstance(scope, PipelineScope) else PipelineScope(scope)

        # ディスパッチテーブルでスコープに対応するハンドラーを取得
        scope_handlers = {
            PipelineScope.FULL: self._execute_full,
            PipelineScope.EXTRACT: self._execute_extract,
            PipelineScope.GENERATE: self._execute_generate,
            PipelineScope.REVIEW: self._execute_review,
            PipelineScope.REFINE: self._execute_refine,
        }

        handler = scope_handlers.get(scope_enum)
        if handler is None:
            raise ValueError(f"Unknown scope: {scope_enum}")

        handler(conn, context, doc_root)
```

### 進捗コールバック

用語抽出・用語集生成・精査ステップでは、処理進捗をリアルタイムでログストリームに送信します。

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

**TermExtractor での使用（バッチ進捗・除外用語）:**
```python
# executor.py
extractor = TermExtractor(
    llm_client=self._llm_client,
    excluded_term_repo=conn,  # common_noun自動除外用
)
progress_cb = self._create_progress_callback(context, "extract")
extracted_terms = extractor.extract_terms(
    documents,
    progress_callback=lambda current, total: progress_cb(current, total, ""),
    return_categories=True,
)
```

**GlossaryGenerator / GlossaryRefiner での使用:**
```python
# executor.py
progress_cb = self._create_progress_callback(context, "provisional")
glossary = generator.generate(
    extracted_terms, documents,
    cancel_event=context.cancel_event,  # キャンセルイベント伝播
    term_progress_callback=progress_cb
)
```

### LLM 処理クラスへのキャンセルイベント伝播

GlossaryGenerator、GlossaryReviewer、GlossaryRefiner は `cancel_event` パラメータを受け取り、ループ内や LLM 呼び出し前にキャンセルチェックを行います。これにより、長時間の LLM 呼び出し中でも迅速にキャンセルが反映されます。

**対応クラスとメソッド:**
```python
# GlossaryGenerator
def generate(
    self,
    term_names: list[str],
    documents: list[Document],
    cancel_event: Event | None = None,      # ← 追加
    term_progress_callback: TermProgressCallback | None = None,
) -> Glossary:
    # ループ前にキャンセルチェック
    if cancel_event is not None and cancel_event.is_set():
        return Glossary()  # 空の用語集を返却

    for i, term_name in enumerate(term_names):
        # 各用語処理前にキャンセルチェック
        if cancel_event is not None and cancel_event.is_set():
            break  # 処理済みの用語のみを含む用語集を返却
        # LLM 呼び出し...

# GlossaryReviewer
def review(
    self,
    glossary: Glossary,
    cancel_event: Event | None = None,
    batch_progress_callback: Callable[[int, int], None] | None = None,  # バッチ進捗
) -> list[GlossaryIssue] | None:  # ← None はキャンセルを意味
    """バッチ処理でレビューを実行（タイムアウト回避）

    大量の用語をレビューする際のタイムアウトやトークン制限を防ぐため、
    用語をバッチに分割（デフォルト10件/バッチ）してLLMに送信します。

    エラー耐性:
        バッチ処理中にエラーが発生した場合（JSON解析失敗、タイムアウト等）、
        そのバッチをスキップして次のバッチに進みます。成功したバッチの
        issuesのみを返却し、パイプライン全体が停止することを防ぎます。

    Args:
        batch_progress_callback: コールバック(current_batch, total_batches)
            各バッチ処理前に呼び出される（ベストエフォート、例外は無視）
    """
    if cancel_event is not None and cancel_event.is_set():
        return None  # キャンセルと「問題なし」を区別

    # バッチに分割して処理
    batches = [terms[i:i+batch_size] for i in range(0, len(terms), batch_size)]
    for batch in batches:
        if cancel_event and cancel_event.is_set():
            return None
        if batch_progress_callback:
            batch_progress_callback(current_batch, total_batches)
        try:
            # LLM 呼び出し（バッチ単位）...
        except Exception:
            # エラー時はスキップして次のバッチへ（警告ログ出力）
            continue

# GlossaryRefiner
def refine(
    self,
    glossary: Glossary,
    issues: list[GlossaryIssue],
    documents: list[Document],
    cancel_event: Event | None = None,      # ← 追加
    progress_callback: TermProgressCallback | None = None,
) -> Glossary:
    if cancel_event is not None and cancel_event.is_set():
        return glossary  # 未改善の用語集を返却
    # ループ内でキャンセルチェック...
```

**戻り値の解釈:**

| クラス | キャンセル時の戻り値 | 通常時との区別 |
|--------|---------------------|----------------|
| GlossaryGenerator | 処理済み用語のみの Glossary | term_count で判断 |
| GlossaryReviewer | `None` | `[]`（問題なし）と区別可能 |
| GlossaryRefiner | 未改善の Glossary | 呼び出し側で判断 |

**Executor での処理:**
```python
# GlossaryReviewer のキャンセル対応
issues = reviewer.review(glossary, cancel_event=context.cancel_event)

# None はキャンセルを意味 → 後続処理をスキップ
if issues is None:
    self._log(context, "info", "Review cancelled")
    return

# issues が空リスト → レビュー完了、問題なし
if not issues:
    # provisional をそのまま refined にコピー...
```

## 遅延キャンセル（Late-Cancel）の処理

パイプライン完了後にキャンセルリクエストが到着した場合の処理方針：

**完了を優先**: パイプラインが実際に完了していれば、ステータスは `completed` となり、結果は保存されます。

**理由**: ユーザーの成果物（用語集）が失われないことを優先。

**実装方法**:
1. `executor.execute()` はキャンセル時に `PipelineCancelledException` を raise
2. `manager._finalize_run_status()` は `isinstance(pipeline_error, PipelineCancelledException)` でキャンセルを判定
3. 各ステップの処理完了後は、キャンセルチェックなしで結果を保存

**シナリオ例**:
```
時系列:
1. パイプライン実行開始
2. パイプライン正常完了（execute が例外なしで終了）
3. ユーザーがキャンセルボタンを押す（遅すぎた）
4. _finalize_run_status で pipeline_error=None なので completed に
5. 結果：ステータスは completed、用語集は保存済み
```

**キャンセルが効くタイミング**:
- 各ステップの開始前（`@_cancellable` デコレータが `PipelineCancelledException` を raise）
- LLM呼び出し前の明示的チェック（`_check_cancellation()` が例外を raise）
- LLM処理クラス内のループ中

**キャンセルが効かないタイミング（完了を優先）**:
- 生成/精査完了後の保存直前

## 実行スコープ

| Scope | 実行ステップ | 用途 |
|-------|------------|------|
| `full` | 1→3→4→5 | generate → review → refine（extractを除く、用語はDB既存前提） |
| `extract` | 2 | 用語抽出のみ（ファイル追加時に自動実行、または手動実行） |
| `generate` | 3 | 用語集生成のみ |
| `review` | 4 | レビューのみ |
| `refine` | 5 | 改善のみ |

**`full` スコープの変更点:**
- extractステップは `full` スコープから除外されています
- `full` 実行時はDBに既に用語が存在していることが前提です
- 用語が0件の場合は `RuntimeError("Cannot execute full pipeline without extracted terms")` が発生します
- extractは以下のタイミングで実行されます:
  - ファイル追加時の自動実行（`triggered_by="auto"`）
  - Terms画面からの手動実行（`scope="extract"`）

**重複用語の処理:**
- 用語抽出ステップ（ステップ2）で LLM が同じ用語を複数回返した場合、重複はスキップされ、ユニークな用語のみが DB に保存されます

**issues の処理パターン:**
- `issues is None`: レビューがキャンセルされた → 後続処理をスキップしてリターン
- `issues == []`: レビュー完了、問題なし → GlossaryRefiner は呼び出さず、provisional をそのまま refined にコピー
- `issues` に要素あり: 問題あり → GlossaryRefiner で改善処理を実行

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

- `full` / `extract` / `refine`: `_load_documents()` を使用してドキュメントを読み込む
- `full`: DBから既存の用語を読み込む（extractはスキップ）。用語が0件の場合はエラー
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

**tests/db/test_runs_repository.py (87 tests)**
- CRUD操作、ステータス遷移、プロジェクト隔離
- update_run_status_if_running（running状態のみ更新）
- complete_run_if_not_cancelled（running状態のみ完了可能）
- fail_run_if_not_terminal（終了状態の上書き防止）
- update_run_status_if_active（汎用ステータス更新関数）
- タイムスタンプ形式の一貫性（UTC ISO 8601形式）
- タイムゾーン検証（naive datetime の拒否）
- ヘルパー関数テスト（_to_iso_string, _current_utc_iso）
- Status Constants テスト（VALID_STATUSES, TERMINAL_STATUSES）
- _validate_status ヘルパー関数テスト
- 各関数の status validation テスト
- error_message 自動クリアテスト

**tests/runs/test_manager.py (87 tests)**
- start_run, cancel_run, スレッド起動、ログキャプチャ
- start_run synchronization（並行呼び出しの競合状態防止）
- per-run cancellation（各runに個別のキャンセルイベント）
- cancellation race condition（キャンセルとステータス更新の競合防止）
- connection error handling（接続エラー時のクリーンアップとフォールバック）
- warning log broadcast（ステータス更新失敗時の警告ログ）
- status misclassification（DB更新失敗時のステータス誤分類防止）
- status update fallback logic（no-opと失敗の区別）
- failed status guard（終了状態への上書き防止）
- state consistency（DB状態とインメモリ状態の整合性）
  - thread start failure edge cases（finished_at設定、_thread リセット、完了シグナル送信、subscriber クリーンアップ、例外マスキング防止）
- cleanup run resources（db_status, status_update_failed パラメータ）
- subscriber late registration（完了後に登録したsubscriberへの完了シグナル送信）
- status update return values（_try_status_with_fallback, _finalize_run_status, _update_failed_status）

**tests/runs/test_executor.py (81 tests)**
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
- `@_cancellable` デコレータテスト
  - エントリーレベルのキャンセルチェック
  - 非キャンセル時の正常実行
  - 位置引数からのcontext検出
- Extract時のuser_notes保持テスト（backup/restore）

**tests/api/routers/test_runs.py (10 tests)**
- API統合テスト（POST/DELETE/GET エンドポイント）

**合計: 265 tests** (Repository 87 + Manager 87 + Executor 81 + API 10)
