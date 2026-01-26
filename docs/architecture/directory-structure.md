# ディレクトリ構成

```
GenGlossary/
├── src/genglossary/              # メインパッケージ
│   ├── __init__.py
│   ├── models/                   # データモデル
│   │   ├── __init__.py
│   │   ├── document.py          # Document, Line管理
│   │   ├── term.py              # Term, TermOccurrence
│   │   ├── glossary.py          # Glossary, GlossaryIssue
│   │   └── project.py           # Project, ProjectStatus
│   ├── llm/                      # LLMクライアント
│   │   ├── __init__.py
│   │   ├── base.py              # BaseLLMClient
│   │   ├── ollama_client.py     # OllamaClient
│   │   ├── openai_compatible_client.py  # OpenAICompatibleClient
│   │   └── factory.py           # LLMクライアントファクトリ
│   ├── db/                       # データベース層 (Schema v3)
│   │   ├── __init__.py
│   │   ├── connection.py        # SQLite接続管理
│   │   ├── schema.py            # スキーマ定義・初期化
│   │   ├── models.py            # DB用TypedDict・シリアライズ
│   │   ├── metadata_repository.py    # メタデータCRUD
│   │   ├── document_repository.py    # ドキュメントCRUD
│   │   ├── term_repository.py   # 抽出用語CRUD
│   │   ├── glossary_helpers.py  # 用語集共通処理
│   │   ├── provisional_repository.py # 暫定用語集CRUD
│   │   ├── issue_repository.py  # 精査結果CRUD
│   │   ├── refined_repository.py     # 最終用語集CRUD
│   │   ├── runs_repository.py   # Run管理CRUD (Schema v3で追加)
│   │   ├── registry_connection.py    # レジストリDB接続管理
│   │   ├── registry_schema.py   # レジストリスキーマ定義
│   │   └── project_repository.py     # プロジェクトCRUD
│   ├── runs/                     # Run管理 (Schema v3で追加)
│   │   ├── __init__.py
│   │   ├── manager.py           # RunManager (スレッド管理)
│   │   └── executor.py          # PipelineExecutor (パイプライン実行)
│   ├── document_loader.py        # ドキュメント読み込み
│   ├── term_extractor.py         # ステップ1: 用語抽出
│   ├── glossary_generator.py     # ステップ2: 用語集生成
│   ├── glossary_reviewer.py      # ステップ3: 精査
│   ├── glossary_refiner.py       # ステップ4: 改善
│   ├── output/
│   │   ├── __init__.py
│   │   └── markdown_writer.py    # Markdown出力
│   ├── api/                       # FastAPI バックエンド
│   │   ├── __init__.py
│   │   ├── app.py                # アプリファクトリ
│   │   ├── dependencies.py       # DI (設定、DB接続、プロジェクト取得)
│   │   ├── schemas/              # APIスキーマ
│   │   │   ├── __init__.py
│   │   │   ├── common.py         # 共通スキーマ (Health, Version, GlossaryTermResponse)
│   │   │   ├── term_schemas.py   # Terms用スキーマ
│   │   │   ├── provisional_schemas.py  # Provisional用スキーマ
│   │   │   ├── issue_schemas.py  # Issues用スキーマ
│   │   │   ├── refined_schemas.py      # Refined用スキーマ
│   │   │   ├── file_schemas.py   # Files用スキーマ
│   │   │   └── run_schemas.py    # Runs用スキーマ (Schema v3)
│   │   ├── middleware/
│   │   │   ├── __init__.py
│   │   │   ├── request_id.py    # リクエストIDミドルウェア
│   │   │   └── logging.py       # 構造化ログミドルウェア
│   │   └── routers/
│   │       ├── __init__.py
│   │       ├── health.py        # /health, /version
│   │       ├── terms.py         # /api/projects/{project_id}/terms
│   │       ├── provisional.py   # /api/projects/{project_id}/provisional
│   │       ├── issues.py        # /api/projects/{project_id}/issues
│   │       ├── refined.py       # /api/projects/{project_id}/refined
│   │       ├── files.py         # /api/projects/{project_id}/files
│   │       └── runs.py          # /api/projects/{project_id}/runs (Schema v3)
│   ├── config.py                 # 設定管理
│   ├── cli.py                    # CLIエントリーポイント (generate)
│   ├── cli_db.py                 # DB管理CLI (db サブコマンド)
│   ├── cli_project.py            # プロジェクト管理CLI (project サブコマンド)
│   └── cli_api.py                # API管理CLI (api サブコマンド)
├── tests/                        # テストコード
│   ├── api/                       # API層テスト
│   │   ├── __init__.py
│   │   ├── conftest.py          # APIテスト用fixture
│   │   ├── test_app.py          # FastAPIアプリテスト
│   │   ├── test_dependencies.py # 依存性注入テスト
│   │   └── routers/             # Routerテスト
│   │       ├── test_terms.py    # Terms APIテスト (8 tests)
│   │       ├── test_provisional.py  # Provisional APIテスト (9 tests)
│   │       ├── test_issues.py   # Issues APIテスト (6 tests)
│   │       ├── test_refined.py  # Refined APIテスト (7 tests)
│   │       ├── test_files.py    # Files APIテスト (11 tests)
│   │       └── test_runs.py     # Runs APIテスト (10 tests, Schema v3)
│   ├── models/
│   │   ├── test_document.py
│   │   ├── test_term.py
│   │   ├── test_glossary.py
│   │   └── test_project.py
│   ├── llm/
│   │   ├── test_base.py
│   │   └── test_ollama_client.py
│   ├── db/                       # DB層テスト
│   │   ├── conftest.py          # DBテスト用fixture
│   │   ├── test_connection.py
│   │   ├── test_schema.py
│   │   ├── test_models.py
│   │   ├── test_metadata_repository.py
│   │   ├── test_document_repository.py
│   │   ├── test_term_repository.py
│   │   ├── test_provisional_repository.py
│   │   ├── test_issue_repository.py
│   │   ├── test_refined_repository.py
│   │   ├── test_runs_repository.py  # Run管理テスト (20 tests, Schema v3)
│   │   ├── test_registry_schema.py
│   │   └── test_project_repository.py
│   ├── runs/                     # Run管理テスト (Schema v3)
│   │   ├── test_manager.py      # RunManagerテスト (13 tests)
│   │   └── test_executor.py     # PipelineExecutorテスト (5 tests)
│   ├── test_document_loader.py
│   ├── test_term_extractor.py
│   ├── test_glossary_generator.py
│   ├── test_glossary_reviewer.py
│   ├── test_glossary_refiner.py
│   ├── test_cli_db.py           # DB CLI統合テスト
│   ├── test_cli_db_regenerate.py # regenerateコマンドテスト
│   ├── test_cli_project.py      # プロジェクトCLI統合テスト
│   └── output/
│       └── test_markdown_writer.py
├── target_docs/                  # 入力ドキュメント
├── output/                       # 生成された用語集
├── scripts/                      # ユーティリティスクリプト
│   └── ticket.sh                # チケット管理
├── .claude/                      # Claudeルール
│   ├── CLAUDE.md
│   └── rules/
├── pyproject.toml                # プロジェクト設定
└── uv.lock                       # 依存関係ロック
```
