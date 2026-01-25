# GUI API データエンドポイント実装計画

## 概要

`tickets/260124-164009-gui-api-data-endpoints.md` の実装計画。
Terms、Provisional、Issues、Refined、Files の各エンティティに対する REST API エンドポイントを追加する。

## ファイル構成

### 新規作成ファイル

```
src/genglossary/api/
├── services/                          # サービス層（新規）
│   ├── __init__.py
│   ├── term_service.py
│   ├── provisional_service.py
│   ├── issue_service.py
│   ├── refined_service.py
│   └── file_service.py
├── routers/
│   ├── terms.py                       # 新規
│   ├── provisional.py                 # 新規
│   ├── issues.py                      # 新規
│   ├── refined.py                     # 新規
│   └── files.py                       # 新規
└── schemas/                           # スキーマ分離（新規）
    ├── __init__.py
    ├── common.py
    ├── term_schemas.py
    ├── provisional_schemas.py
    ├── issue_schemas.py
    ├── refined_schemas.py
    └── file_schemas.py

tests/api/
├── services/                          # サービス層テスト（新規）
│   ├── test_term_service.py
│   ├── test_provisional_service.py
│   ├── test_issue_service.py
│   ├── test_refined_service.py
│   └── test_file_service.py
└── routers/                           # Router統合テスト（新規）
    ├── test_terms.py
    ├── test_provisional.py
    ├── test_issues.py
    ├── test_refined.py
    └── test_files.py
```

### 更新ファイル

- `src/genglossary/api/dependencies.py` - プロジェクトDB接続の依存性注入を追加
- `src/genglossary/api/app.py` - 新規Routerの登録
- `src/genglossary/api/routers/__init__.py` - Router export追加
- `tests/api/conftest.py` - テスト用fixture追加
- `docs/architecture.md` - API仕様を追記

## API エンドポイント一覧

| エンドポイント | メソッド | 説明 |
|---------------|---------|------|
| `/api/projects/{project_id}/terms` | GET | 抽出用語一覧取得 |
| `/api/projects/{project_id}/terms/{term_id}` | GET | 用語詳細取得 |
| `/api/projects/{project_id}/terms` | POST | 用語手動追加 |
| `/api/projects/{project_id}/terms/{term_id}` | PATCH | 用語編集 |
| `/api/projects/{project_id}/terms/{term_id}` | DELETE | 用語除外 |
| `/api/projects/{project_id}/provisional` | GET | 暫定用語集一覧 |
| `/api/projects/{project_id}/provisional/{entry_id}` | PATCH | 定義・confidence編集 |
| `/api/projects/{project_id}/provisional/{entry_id}/regenerate` | POST | 単一再生成 |
| `/api/projects/{project_id}/issues` | GET | 精査結果一覧（issue_typeフィルタ対応） |
| `/api/projects/{project_id}/refined` | GET | 最終用語集一覧 |
| `/api/projects/{project_id}/refined/export-md` | GET | Markdownエクスポート |
| `/api/projects/{project_id}/files` | GET | 登録文書一覧 |
| `/api/projects/{project_id}/files` | POST | ファイル追加 |
| `/api/projects/{project_id}/files/{file_id}` | DELETE | ファイル削除 |
| `/api/projects/{project_id}/files/diff-scan` | POST | 差分スキャン |

## 依存性注入パターン

```python
# dependencies.py に追加
def get_registry_db() -> Generator[sqlite3.Connection, None, None]:
    """レジストリDB接続を取得"""
    ...

def get_project_by_id(project_id: int, registry_conn) -> Project:
    """プロジェクトIDからProjectを取得（404対応）"""
    ...

def get_project_db(project: Project) -> Generator[sqlite3.Connection, None, None]:
    """プロジェクト固有のDB接続を取得"""
    ...
```

## 実装フェーズ（TDDサイクル）

### Phase 1: 基盤準備
1. `dependencies.py` にプロジェクトDB接続の依存性注入を追加
2. `schemas/common.py` を作成
3. `services/__init__.py` を作成
4. `tests/api/conftest.py` にテスト用fixture追加

### Phase 2: Terms API（TDD）
1. **Red**: `tests/api/test_data_endpoints.py` にTerms APIテスト作成
2. テスト失敗を確認
3. **Green**:
   - `schemas/term_schemas.py` 作成
   - `services/term_service.py` 作成
   - `routers/terms.py` 作成
   - `app.py` にルーター登録
4. テスト通過を確認

### Phase 3: Provisional API（TDD）
- 同様のTDDサイクル
- regenerateはLLM呼び出しのモック必要

### Phase 4: Issues API（TDD）
- 同様のTDDサイクル
- issue_typeフィルタのクエリパラメータ対応

### Phase 5: Refined API（TDD）
- 同様のTDDサイクル
- export-mdはMarkdownレスポンス

### Phase 6: Files API（TDD）
- 同様のTDDサイクル
- diff-scanはファイルシステム操作

### Phase 7: 完了処理
1. `docs/architecture.md` 更新
2. `uv run pyright` 実行（エラーゼロ）
3. `uv run pytest` 実行（全テスト通過）
4. code-simplifier agent でコードレビュー
5. 開発者承認

## 重要なファイル参照

| ファイル | 役割 |
|---------|------|
| `src/genglossary/api/dependencies.py` | 依存性注入のコアロジック |
| `src/genglossary/db/project_repository.py` | `get_project()` 関数 |
| `src/genglossary/db/term_repository.py` | Terms APIの基盤リポジトリ |
| `src/genglossary/db/provisional_repository.py` | Provisional APIの基盤リポジトリ |
| `src/genglossary/db/issue_repository.py` | Issues APIの基盤リポジトリ |
| `src/genglossary/db/refined_repository.py` | Refined APIの基盤リポジトリ |
| `src/genglossary/db/document_repository.py` | Files APIの基盤リポジトリ |
| `src/genglossary/api/routers/health.py` | Routerパターンの参考 |
| `tests/api/conftest.py` | テストfixture参考 |

## 検証方法

### 自動テスト
```bash
uv run pytest tests/api/ -v
```

### 静的解析
```bash
uv run pyright
```

### 手動テスト（APIサーバー起動）
```bash
uv run genglossary api serve --reload
# 別ターミナルで
curl http://localhost:8000/api/projects/1/terms
```

## 注意事項

- 各リポジトリ関数は `sqlite3.Connection` を第一引数に取る
- プロジェクトごとに別々のDBファイルを使用
- Terms/Issues は `sqlite3.Row` を返却、Provisional/Refined は `GlossaryTermRow` (TypedDict) を返却
- regenerate エンドポイントはLLM呼び出しを伴うため、テストではモックが必要
