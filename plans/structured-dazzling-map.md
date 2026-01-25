# コードレビュー指摘事項の修正計画

## 概要

コードレビューで指摘された2つの問題と、オープンクエスチョンへの対応を実施する。

## 修正対象

### 1. トランザクション問題の修正

**問題**: レジストリ挿入がコミットされた後にプロジェクトDB初期化が失敗すると、不整合なレコードが残る

**修正箇所**: `src/genglossary/db/project_repository.py`

**修正方針**:
- プロジェクトDBを先に作成・初期化し、成功後にレジストリに挿入する
- 順序を逆にすることで、DBの作成失敗時にレジストリが汚染されない

```python
# Before (問題あり)
cursor.execute("INSERT ...")
conn.commit()  # 先にコミット
project_conn = get_connection(db_path)
initialize_db(project_conn)  # ここで失敗すると不整合

# After (修正後)
project_conn = get_connection(db_path)
initialize_db(project_conn)  # 先にDB作成
project_conn.close()
cursor.execute("INSERT ...")
conn.commit()  # 成功後にコミット
```

### 2. 相対パス問題の修正

**問題**: `--registry`が相対パスの場合、`db_path`も相対パスになりCWD依存になる

**修正箇所**: `src/genglossary/cli_project.py`

**修正方針**:
- `_get_project_db_path`で`.resolve()`を使用して絶対パスに変換

```python
def _get_project_db_path(registry: Path | None, project_name: str) -> Path:
    projects_dir = _get_projects_dir(registry)
    db_path = projects_dir / project_name / "project.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path.resolve()  # 絶対パスに変換
```

### 3. project clone でDBコピー

**問題**: 現在の`clone`は設定のみコピーし、DBは新規初期化される

**修正箇所**:
- `src/genglossary/db/project_repository.py` の `clone_project`
- `src/genglossary/cli_project.py` の `clone` コマンド

**修正方針**:
- ソースプロジェクトのDBファイルを新しい場所にコピーする
- `shutil.copy2`を使用してファイルをコピー

## TDDアプローチ

### Red フェーズ: テスト追加

1. **トランザクション問題のテスト** (`tests/db/test_project_repository.py`)
   - プロジェクトDB作成失敗時にレジストリが汚染されないことを確認

2. **相対パス問題のテスト** (`tests/test_cli_project.py`)
   - 相対パスのregistryを使用した場合でも絶対パスが保存されることを確認

3. **DBコピーのテスト** (`tests/db/test_project_repository.py`)
   - `clone_project`後にソースDBの内容が新DBにコピーされていることを確認

### Green フェーズ: 実装

テストが失敗することを確認後、上記の修正を実装

## 修正ファイル一覧

- `src/genglossary/db/project_repository.py` - create_project, clone_project
- `src/genglossary/cli_project.py` - _get_project_db_path

## 検証方法

```bash
# テスト実行
uv run pytest tests/db/test_project_repository.py tests/test_cli_project.py -v

# 全テスト実行
uv run pytest

# 静的解析
uv run pyright
```
