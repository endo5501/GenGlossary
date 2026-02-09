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
│   │   ├── project.py           # Project, ProjectStatus
│   │   ├── term_validator.py    # 共通バリデータ (ExcludedTerm/RequiredTerm用)
│   │   └── synonym.py          # SynonymGroup, SynonymMember
│   ├── llm/                      # LLMクライアント
│   │   ├── __init__.py
│   │   ├── base.py              # BaseLLMClient (自動デバッグラップ付き)
│   │   ├── ollama_client.py     # OllamaClient
│   │   ├── openai_compatible_client.py  # OpenAICompatibleClient
│   │   ├── debug_logger.py      # LlmDebugLogger (プロンプト・レスポンスのファイル出力)
│   │   └── factory.py           # LLMクライアントファクトリ
│   ├── db/                       # データベース層 (Schema v9)
│   │   ├── __init__.py
│   │   ├── connection.py        # SQLite接続管理
│   │   ├── schema.py            # スキーマ定義・初期化
│   │   ├── models.py            # DB用TypedDict・シリアライズ
│   │   ├── metadata_repository.py    # メタデータCRUD
│   │   ├── document_repository.py    # ドキュメントCRUD
│   │   ├── term_repository.py   # 抽出用語CRUD
│   │   ├── generic_term_repository.py # 除外/必須用語 共通CRUD
│   │   ├── excluded_term_repository.py # 除外用語CRUD (薄いラッパー)
│   │   ├── required_term_repository.py # 必須用語CRUD (薄いラッパー)
│   │   ├── glossary_helpers.py  # 用語集共通処理
│   │   ├── provisional_repository.py # 暫定用語集CRUD
│   │   ├── issue_repository.py  # 精査結果CRUD
│   │   ├── refined_repository.py     # 最終用語集CRUD
│   │   ├── runs_repository.py   # Run管理CRUD (Schema v3で追加)
│   │   ├── synonym_repository.py # 同義語グループCRUD
│   │   ├── registry_connection.py    # レジストリDB接続管理
│   │   ├── registry_schema.py   # レジストリスキーマ定義
│   │   └── project_repository.py     # プロジェクトCRUD
│   ├── runs/                     # Run管理 (Schema v3で追加)
│   │   ├── __init__.py
│   │   ├── manager.py           # RunManager (スレッド管理)
│   │   ├── executor.py          # PipelineExecutor (パイプライン実行)
│   │   └── error_sanitizer.py   # エラーメッセージのサニタイズ
│   ├── document_loader.py        # ドキュメント読み込み
│   ├── term_extractor.py         # ステップ1: 用語抽出
│   ├── glossary_generator.py     # ステップ2: 用語集生成
│   ├── glossary_reviewer.py      # ステップ3: 精査
│   ├── glossary_refiner.py       # ステップ4: 改善
│   ├── synonym_utils.py          # 同義語ルックアップ共通ユーティリティ
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
│   │   │   ├── term_base_schemas.py   # 除外/必須用語 共通ベーススキーマ
│   │   │   ├── excluded_term_schemas.py # 除外用語スキーマ (ベース継承)
│   │   │   ├── required_term_schemas.py # 必須用語スキーマ (ベース継承)
│   │   │   ├── term_schemas.py   # Terms用スキーマ
│   │   │   ├── provisional_schemas.py  # Provisional用スキーマ
│   │   │   ├── issue_schemas.py  # Issues用スキーマ
│   │   │   ├── refined_schemas.py      # Refined用スキーマ
│   │   │   ├── file_schemas.py   # Files用スキーマ
│   │   │   ├── run_schemas.py    # Runs用スキーマ (Schema v3)
│   │   │   └── synonym_group_schemas.py # 同義語グループスキーマ
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
│   │       ├── runs.py          # /api/projects/{project_id}/runs (Schema v3)
│   │       └── synonym_groups.py # /api/projects/{project_id}/synonym-groups
│   ├── config.py                 # 設定管理
│   ├── utils/                    # ユーティリティモジュール
│   │   ├── __init__.py
│   │   ├── callback.py           # コールバック安全呼び出し
│   │   ├── hash.py               # ハッシュユーティリティ
│   │   ├── token_counter.py      # トークンカウント
│   │   └── text.py               # テキスト処理（CJK検出等）
│   ├── exceptions.py             # カスタム例外
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
│   │   ├── test_project.py
│   │   └── test_term_validator.py  # 共通バリデータテスト
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
│   │   ├── test_generic_term_repository.py  # 共通リポジトリテスト
│   │   ├── test_provisional_repository.py
│   │   ├── test_issue_repository.py
│   │   ├── test_refined_repository.py
│   │   ├── test_runs_repository.py  # Run管理テスト (20 tests, Schema v3)
│   │   ├── test_registry_schema.py
│   │   ├── test_project_repository.py
│   │   └── test_synonym_repository.py
│   ├── runs/                     # Run管理テスト (Schema v3)
│   │   ├── test_manager.py      # RunManagerテスト (92 tests)
│   │   ├── test_executor.py     # PipelineExecutorテスト (81 tests)
│   │   └── test_error_sanitizer.py  # エラーサニタイズテスト (28 tests)
│   ├── test_document_loader.py
│   ├── test_term_extractor.py
│   ├── test_glossary_generator.py
│   ├── test_glossary_reviewer.py
│   ├── test_glossary_refiner.py
│   ├── test_cli_db.py           # DB CLI統合テスト
│   ├── test_cli_db_regenerate.py # regenerateコマンドテスト
│   ├── test_cli_project.py      # プロジェクトCLI統合テスト
│   ├── test_callback.py         # コールバックユーティリティテスト
│   ├── test_text_utils.py       # テキストユーティリティテスト
│   ├── test_token_counter.py    # トークンカウントテスト
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

## フロントエンド（frontend/）

React SPA のディレクトリ構成。

```
frontend/
├── src/
│   ├── __tests__/           # テストコード
│   │   ├── setup.ts         # テストセットアップ
│   │   ├── test-utils.tsx   # テストユーティリティ
│   │   ├── api-client.test.ts   # APIクライアントテスト (14 tests)
│   │   ├── app-shell.test.tsx   # レイアウトテスト (19 tests)
│   │   └── routing.test.tsx     # ルーティングテスト (16 tests)
│   ├── api/                 # API通信層
│   │   ├── client.ts        # HTTPクライアント (ApiError, apiClient)
│   │   ├── types.ts         # 型定義 (FileResponse, TermResponse, etc.)
│   │   └── hooks/           # TanStack Queryフック
│   │       ├── index.ts
│   │       ├── useTermsCrud.ts     # 共通用語CRUDフック (ジェネリック)
│   │       ├── useExcludedTerms.ts # 除外用語フック (薄いラッパー)
│   │       └── useRequiredTerms.ts # 必須用語フック (薄いラッパー)
│   ├── components/          # Reactコンポーネント
│   │   ├── common/
│   │   │   ├── PagePlaceholder.tsx  # 未実装ページ用
│   │   │   ├── PageContainer.tsx    # ページ共通コンテナ (loading/error/empty)
│   │   │   ├── SplitLayout.tsx      # リスト・詳細の左右分割レイアウト
│   │   │   ├── OccurrenceList.tsx   # 用語出現箇所リスト
│   │   │   ├── AddTermModal.tsx     # 用語追加モーダル (除外/必須共通)
│   │   │   └── TermListTable.tsx    # 用語一覧テーブル (除外/必須共通)
│   │   └── layout/
│   │       ├── index.ts
│   │       ├── AppShell.tsx      # メインレイアウト
│   │       ├── GlobalTopBar.tsx  # ヘッダー
│   │       ├── LeftNavRail.tsx   # 左ナビゲーション
│   │       └── LogPanel.tsx      # ログビューア
│   ├── utils/               # ユーティリティ
│   │   ├── extractProjectId.ts # URLからプロジェクトID抽出
│   │   ├── colors.ts        # カラーユーティリティ
│   │   ├── termUtils.ts     # 用語関連ユーティリティ
│   │   └── getRowSelectionProps.ts # テーブル行選択ヘルパー
│   ├── routes/              # ルーティング設定
│   │   └── index.tsx        # TanStack Routerルート定義
│   ├── theme/               # テーマ設定
│   │   └── theme.ts         # Mantineテーマ
│   └── main.tsx             # エントリーポイント
├── index.html               # HTMLテンプレート
├── package.json             # 依存関係・スクリプト
├── tsconfig.json            # TypeScript設定
├── vite.config.ts           # Vite設定
├── vitest.config.ts         # Vitest設定
└── eslint.config.js         # ESLint設定
```
