# FastAPI Backend Scaffold 実装計画

**チケット**: `tickets/260124-164005-gui-backend-scaffold.md`

## 概要

GUIのためのFastAPIバックエンドの基盤を構築する。`/health`、`/version`エンドポイント、CORSミドルウェア、リクエストIDミドルウェアを実装し、CLIから`genglossary api serve`で起動できるようにする。

## ディレクトリ構成

```
src/genglossary/
├── api/                          # NEW
│   ├── __init__.py
│   ├── app.py                    # FastAPIアプリファクトリ
│   ├── dependencies.py           # DI（DB接続、設定）
│   ├── schemas.py                # APIレスポンススキーマ
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── request_id.py         # リクエストIDミドルウェア
│   │   └── logging.py            # 構造化ログミドルウェア
│   └── routers/
│       ├── __init__.py
│       └── health.py             # /health, /version

tests/
├── api/                          # NEW
│   ├── __init__.py
│   ├── conftest.py               # APIテスト用fixture
│   └── test_app.py               # メインテスト
```

## 実装ステップ

### Phase 1: TDD Red（テスト先行）

1. **依存関係の追加** (`pyproject.toml`)
   ```toml
   dependencies = [
       # 既存の依存関係...
       "fastapi>=0.115.0",
       "uvicorn[standard]>=0.34.0",
   ]
   ```
   - `uv add fastapi "uvicorn[standard]"` を実行

2. **テストファイル作成**
   - `tests/api/__init__.py`
   - `tests/api/conftest.py` - TestClient fixture
   - `tests/api/test_app.py` - 以下のテストケース:
     - `/health` が200とJSON返却
     - `/version` がパッケージバージョンを返却
     - CORSヘッダーが付与される（localhost:3000, 127.0.0.1:3000など）
     - X-Request-IDヘッダーがUUID形式で付与
     - OpenAPI（/openapi.json, /docs, /redoc）がアクセス可能

3. **テスト失敗を確認**
   - `uv run pytest tests/api/ -v`

### Phase 2: TDD Green（実装）

4. **スキーマ定義** (`src/genglossary/api/schemas.py`)
   - `HealthResponse(status, timestamp)`
   - `VersionResponse(name, version)`

5. **ミドルウェア実装**
   - `src/genglossary/api/middleware/__init__.py`
   - `src/genglossary/api/middleware/request_id.py`
     - UUIDを生成し、X-Request-IDヘッダーに付与
     - request.stateにも保存（ログ用）
   - `src/genglossary/api/middleware/logging.py`
     - リクエスト/レスポンスを構造化ログ出力

6. **ルーター実装** (`src/genglossary/api/routers/health.py`)
   - `GET /health` → HealthResponse
   - `GET /version` → VersionResponse（`genglossary.__version__`を使用）

7. **依存性注入** (`src/genglossary/api/dependencies.py`)
   - `get_config()` - 既存のConfig()を返す
   - `get_db_connection()` - プレースホルダー（後続チケットで拡張）

8. **アプリファクトリ** (`src/genglossary/api/app.py`)
   ```python
   def create_app() -> FastAPI:
       app = FastAPI(
           title="GenGlossary API",
           description="API for GenGlossary",
           version=__version__,
       )
       # CORSミドルウェア（localhost:3000, 5173, 127.0.0.1:3000, 5173）
       # RequestIDミドルウェア
       # StructuredLoggingミドルウェア
       # health router
       return app
   ```

9. **パッケージ初期化** (`src/genglossary/api/__init__.py`)

### Phase 3: CLI統合

10. **CLIコマンド追加** (`src/genglossary/cli.py`)
    - `main`グループに`api`サブグループを追加
    - `api serve`コマンド（--host, --port, --reload オプション）
    - uvicornで`create_app`をファクトリモードで起動

### Phase 4: ドキュメント・仕上げ

11. **docs/architecture.md更新**
    - API層の説明を追加
    - 依存関係図を更新

12. **静的解析・テスト**
    - `uv run pyright src/`
    - `uv run pytest`

## 重要なファイル

| ファイル | 役割 |
|---------|------|
| `src/genglossary/api/app.py` | FastAPIアプリファクトリ（中核） |
| `tests/api/test_app.py` | 全要件のテスト |
| `src/genglossary/cli.py:702-708` | コマンド登録パターン参照 |
| `src/genglossary/config.py` | 設定パターン参照 |
| `src/genglossary/db/connection.py` | DB接続共有パターン参照 |

## コミット戦略

1. **テスト追加** - "Add tests for FastAPI backend scaffold (TDD Red)"
2. **API実装** - "Implement FastAPI backend with health/version endpoints"
3. **CLI統合** - "Add api serve CLI command"
4. **ドキュメント** - "Update architecture docs for API layer"

## 検証方法

1. テスト実行
   ```bash
   uv run pytest tests/api/ -v
   ```

2. サーバー起動確認
   ```bash
   uv run genglossary api serve
   # 別ターミナルで:
   curl http://localhost:8000/health
   curl http://localhost:8000/version
   curl http://localhost:8000/openapi.json
   ```

3. CORSヘッダー確認
   ```bash
   curl -i -X OPTIONS http://localhost:8000/health \
     -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: GET"
   ```

4. リクエストID確認
   ```bash
   curl -i http://localhost:8000/health
   # X-Request-ID ヘッダーがUUID形式であること
   ```

5. 全テスト・静的解析
   ```bash
   uv run pytest
   uv run pyright src/
   ```
