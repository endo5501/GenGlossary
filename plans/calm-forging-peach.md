# GUI API Operations Runner 実装計画

## 概要

既存のCLIパイプライン（extract → provisional → issues → refined）をAPI経由で実行可能にし、バックグラウンドタスク管理とリアルタイムログストリーミングを実装する。

## 新規ファイル構成

```
src/genglossary/
├── api/
│   ├── routers/
│   │   └── runs.py                    # 新規: Run APIエンドポイント
│   └── schemas/
│       └── run_schemas.py             # 新規: Run リクエスト/レスポンススキーマ
├── db/
│   └── runs_repository.py             # 新規: Run CRUD操作
└── runs/
    ├── __init__.py                    # 新規: パッケージ初期化
    ├── manager.py                     # 新規: RunManagerクラス
    ├── executor.py                    # 新規: パイプライン実行ロジック
    └── log_capture.py                 # 新規: ログキャプチャ/ストリーミング

tests/
├── api/routers/
│   └── test_runs.py                   # 新規: Run APIテスト
├── db/
│   └── test_runs_repository.py        # 新規: Run repositoryテスト
└── runs/
    ├── test_manager.py                # 新規: RunManagerテスト
    └── test_executor.py               # 新規: Executorテスト
```

## 既存ファイルの変更

| ファイル | 変更内容 |
|---------|---------|
| `src/genglossary/db/schema.py` | `runs`テーブルを追加、SCHEMA_VERSION更新 |
| `src/genglossary/api/app.py` | `runs_router`をインポート・登録 |
| `src/genglossary/api/routers/__init__.py` | `runs_router`をエクスポート |
| `docs/architecture.md` | Run管理セクションを追加 |

## データベーススキーマ

### runs テーブル（プロジェクトDB内）

```sql
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scope TEXT NOT NULL,              -- 'full', 'from_terms', 'provisional_to_refined'
    status TEXT NOT NULL DEFAULT 'pending',  -- 'pending', 'running', 'completed', 'failed', 'cancelled'
    started_at TEXT,
    finished_at TEXT,
    triggered_by TEXT NOT NULL DEFAULT 'api',
    error_message TEXT,
    progress_current INTEGER DEFAULT 0,
    progress_total INTEGER DEFAULT 0,
    current_step TEXT,                -- 'terms', 'provisional', 'issues', 'refined'
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

## APIエンドポイント

| メソッド | パス | 説明 |
|---------|------|------|
| POST | `/api/projects/{project_id}/runs` | 新規Run開始（scope: full/from_terms/provisional_to_refined） |
| DELETE | `/api/projects/{project_id}/runs/{run_id}` | Runキャンセル |
| GET | `/api/projects/{project_id}/runs` | Run履歴一覧 |
| GET | `/api/projects/{project_id}/runs/current` | 現在アクティブなRun |
| GET | `/api/projects/{project_id}/runs/{run_id}` | Run詳細取得 |
| GET | `/api/projects/{project_id}/runs/{run_id}/logs` | ログストリーミング（SSE） |

## コア設計

### RunManager（スレッドベース）

- プロジェクトごとに1つのアクティブRunのみ許可
- `threading.Thread`でバックグラウンド実行
- `threading.Event`でキャンセル通知
- `queue.Queue`でログメッセージを転送

### PipelineExecutor

- 既存CLIロジックを再利用（TermExtractor, GlossaryGenerator, GlossaryReviewer, GlossaryRefiner）
- 各ステップでキャンセルチェック
- 進捗とログをキューに送信

### SSEログストリーミング

```
data: {"level": "info", "message": "Starting term extraction..."}
data: {"level": "info", "message": "Extracted 25 terms"}
: keepalive
event: complete
data: {}
```

## 実装ステップ（TDD）

### Step 1: Red - テスト作成
1. `tests/db/test_runs_repository.py` - Repository CRUDテスト
2. `tests/runs/test_manager.py` - RunManager start/cancel/get テスト
3. `tests/api/routers/test_runs.py` - APIエンドポイントテスト

### Step 2: Green - 実装
1. `src/genglossary/db/schema.py` - runsテーブル追加
2. `src/genglossary/db/runs_repository.py` - CRUD関数実装
3. `src/genglossary/runs/manager.py` - RunManager実装
4. `src/genglossary/runs/executor.py` - PipelineExecutor実装
5. `src/genglossary/runs/log_capture.py` - SSEストリーミング実装
6. `src/genglossary/api/schemas/run_schemas.py` - スキーマ定義
7. `src/genglossary/api/routers/runs.py` - APIエンドポイント実装
8. `src/genglossary/api/app.py` - ルーター登録

### Step 3: 検証
1. `uv run pytest` - 全テスト通過確認
2. `uv run pyright` - 静的解析通過確認
3. `docs/architecture.md` 更新

## 検証方法

### 単体テスト
```bash
uv run pytest tests/db/test_runs_repository.py -v
uv run pytest tests/runs/ -v
uv run pytest tests/api/routers/test_runs.py -v
```

### 統合テスト（手動）
```bash
# APIサーバー起動
uv run genglossary api

# プロジェクト作成 & Run開始
curl -X POST http://localhost:8000/api/projects/1/runs -H "Content-Type: application/json" -d '{"scope": "full"}'

# ログストリーミング確認
curl -N http://localhost:8000/api/projects/1/runs/1/logs

# Run状態確認
curl http://localhost:8000/api/projects/1/runs/current

# Runキャンセル
curl -X DELETE http://localhost:8000/api/projects/1/runs/1
```

## 注意事項

- LLM呼び出しはモックでテスト（respx使用）
- プロジェクト隔離を維持（他プロジェクトのRunに影響しない）
- グレースフルシャットダウン対応
- SSEはシンプル優先、将来WebSocketへの移行余地を残す
