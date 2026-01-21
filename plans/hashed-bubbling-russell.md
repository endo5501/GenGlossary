# Phase 2 実装計画: CLI更新とregenerateコマンド実装

## 概要

チケット `260120-phase2-cli-regenerate` の実装計画。Phase 1（Schema v2）は完了済みだが、CLI層（cli_db.py, cli.py）とテスト（test_cli_db.py）は古いSchema v1のままであるため、更新が必要。

## 現状の問題

| ファイル | 問題 | 主要箇所 |
|----------|------|----------|
| `cli_db.py` | `run_repository` をインポート（存在しない）| L22 |
| `cli.py` | `run_repository` をインポート（存在しない）| L20, L169, L183-188, L230-356 |
| `test_cli_db.py` | `create_run()` を使用、`--run-id` をテスト | L10, L78, L85以降 |

## 実装手順

### Phase 3: CLI更新（TDD）

#### Step 1: テストの修正（RED → GREEN → COMMIT）

**ファイル:** `tests/test_cli_db.py`

1. 削除するimport:
   - `from genglossary.db.run_repository import create_run`

2. 削除するテストクラス:
   - `TestDbRunsList`
   - `TestDbRunsShow`
   - `TestDbRunsLatest`

3. 修正するテスト:
   - 全テストから `create_run()` 呼び出しを削除
   - 全テストから `--run-id` オプションを削除
   - `create_term(conn, run_id, ...)` → `create_term(conn, ...)`

4. 追加するテストクラス:
   - `TestDbInfo` - メタデータ表示のテスト
   - `TestDbIssuesList` - issues listのテスト

#### Step 2: cli_db.pyの更新

**ファイル:** `src/genglossary/cli_db.py`

1. import文の修正:
   - `run_repository` のimportを削除
   - `list_terms_by_run` → `list_all_terms`
   - `list_provisional_terms_by_run` → `list_all_provisional`
   - `list_refined_terms_by_run` → `list_all_refined`
   - `metadata_repository`, `issue_repository` を追加

2. 削除するコマンド:
   - `db runs` グループ全体（list, show, latest）

3. 修正するコマンド:
   - `terms list` - `--run-id` 削除
   - `terms import` - `--run-id` 削除
   - `provisional list` - `--run-id` 削除
   - `refined list` - `--run-id` 削除
   - `refined export-md` - `--run-id` 削除

4. 追加するコマンド:
   - `db info` - メタデータ表示
   - `issues list` - 精査結果一覧

#### Step 3: cli.pyの更新

**ファイル:** `src/genglossary/cli.py`

1. `run_repository` のimportを削除
2. `create_run()`, `complete_run()`, `fail_run()` の使用を削除
3. `upsert_metadata()` を使用するように変更

### Phase 4: regenerateコマンド実装（TDD）

#### Step 4: regenerateテストの作成

**新規ファイル:** `tests/test_cli_db_regenerate.py`

テストクラス:
- `TestTermsRegenerate`
- `TestProvisionalRegenerate`
- `TestIssuesRegenerate`
- `TestRefinedRegenerate`

LLMモック戦略:
```python
@patch("genglossary.cli_db.create_llm_client")
@patch("genglossary.cli_db.TermExtractor")
def test_regenerate(mock_extractor_class, mock_create_client):
    mock_llm = MagicMock()
    mock_llm.is_available.return_value = True
    mock_create_client.return_value = mock_llm
    ...
```

#### Step 5: regenerateコマンドの実装

**ファイル:** `src/genglossary/cli_db.py`

| コマンド | 処理 |
|----------|------|
| `terms regenerate --input <dir>` | 用語削除 → ドキュメント読込 → TermExtractor → DB保存 |
| `provisional regenerate` | 暫定用語削除 → terms取得 → GlossaryGenerator → DB保存 |
| `issues regenerate` | issues削除 → provisional取得 → GlossaryReviewer → DB保存 |
| `refined regenerate` | refined削除 → provisional/issues取得 → GlossaryRefiner → DB保存 |

共通オプション:
- `--llm-provider` (ollama/openai)
- `--model`
- `--db-path`

## 変更ファイル一覧

| ファイル | 変更内容 |
|----------|----------|
| `src/genglossary/cli_db.py` | runs削除、--run-id削除、info/issues list追加、regenerate追加 |
| `src/genglossary/cli.py` | run_repository依存削除 |
| `tests/test_cli_db.py` | runs tests削除、--run-id削除、info/issues tests追加 |
| `tests/test_cli_db_regenerate.py` | 新規作成 |

## 検証方法

### Phase 3検証

```bash
# テスト実行
uv run pytest tests/test_cli_db.py -v

# CLI動作確認
uv run genglossary db init --db-path ./test.db
uv run genglossary db info --db-path ./test.db
uv run genglossary db terms list --db-path ./test.db
uv run genglossary db issues list --db-path ./test.db

# runsが削除されていることを確認
uv run genglossary db runs list  # エラーになるはず
```

### Phase 4検証

```bash
# regenerateテスト
uv run pytest tests/test_cli_db_regenerate.py -v

# 全テスト
uv run pytest -v

# 型チェック
uv run pyright
```

## リスクと対策

| リスク | 対策 |
|--------|------|
| cli.pyの修正で既存機能が壊れる | Phase 3完了前に全テストパスを確認 |
| regenerateが既存データを誤削除 | 削除前にclear関数を使用、テストで検証 |
| ドキュメントパス不一致 | FileNotFoundをハンドリング、警告表示 |
