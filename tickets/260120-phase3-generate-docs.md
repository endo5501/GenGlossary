---
priority: 2
tags: [cli, generate, docs]
description: "Phase 5-6: generateコマンドのDB保存必須化とドキュメント更新"
created_at: "2026-01-20T02:05:50Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# Phase 5-6: generateコマンドのDB保存必須化とドキュメント更新

親チケット: 260120-020550-db-regenerate-commands
依存: 260120-phase2-cli-regenerate

## 概要

`generate` コマンドでDB保存をデフォルト有効化し、全テストとドキュメントを更新します。

## Phase 5: generate コマンドのDB保存必須化

### 変更点

- `--db-path` のデフォルト値を `./genglossary.db` に変更
- `--no-db` フラグ追加でDB保存スキップ可能
- run_id 関連コードを削除
- metadata テーブルに実行情報を保存

### 現在の動作

```bash
# DB保存しない（デフォルト）
genglossary generate --input ./target_docs --output ./output/glossary.md

# DB保存する（--db-path指定時のみ）
genglossary generate --input ./target_docs --output ./output/glossary.md --db-path ./genglossary.db
```

### 新しい動作

```bash
# DB保存する（デフォルト）
genglossary generate --input ./target_docs --output ./output/glossary.md
# → ./genglossary.db に保存される

# DB保存しない（--no-db指定時のみ）
genglossary generate --input ./target_docs --output ./output/glossary.md --no-db

# カスタムDBパス指定
genglossary generate --input ./target_docs --output ./output/glossary.md --db-path ./custom.db
```

### 実装の変更

**変更前:**
```python
@click.command()
@click.option("--input", required=True, help="Input file or directory")
@click.option("--output", default="output/glossary.md", help="Output file")
@click.option("--db-path", default=None, help="Database path (optional)")
@click.option("--llm-provider", default="ollama", help="LLM provider")
@click.option("--model", default="llama3", help="Model name")
def generate(
    input: str,
    output: str,
    db_path: str | None,
    llm_provider: str,
    model: str
) -> None:
    """Generate glossary from documents."""
    # DB保存は db_path が指定された場合のみ
    if db_path:
        # run_id を作成
        run_id = create_run(conn, input, llm_provider, model)
        # 各ステップで run_id を使用
```

**変更後:**
```python
@click.command()
@click.option("--input", required=True, help="Input file or directory")
@click.option("--output", default="output/glossary.md", help="Output file")
@click.option("--db-path", default="./genglossary.db", help="Database path")
@click.option("--no-db", is_flag=True, help="Skip database saving")
@click.option("--llm-provider", default="ollama", help="LLM provider")
@click.option("--model", default="llama3", help="Model name")
def generate(
    input: str,
    output: str,
    db_path: str,
    no_db: bool,
    llm_provider: str,
    model: str
) -> None:
    """Generate glossary from documents."""
    # --no-db が指定されていない限り、常にDB保存
    if not no_db:
        conn = get_connection(db_path)
        initialize_db(conn)
        # metadata を更新（run_id不要）
        upsert_metadata(conn, input_path=input, llm_provider=llm_provider, llm_model=model)
        # 各ステップで run_id を使用せずに保存
```

### 各ステップの保存処理

#### ステップ1: 用語抽出

```python
# ドキュメント保存
for doc in documents:
    create_document(conn, doc.file_path, compute_hash(doc.content))

# 用語保存（run_id不要）
for term in extracted_terms:
    create_term(conn, term_text=term, category=None)
```

#### ステップ2: 用語集生成

```python
# 暫定用語集保存（run_id不要）
for term in glossary.terms:
    create_provisional_term(
        conn,
        term_name=term.text,
        definition=term.definition,
        confidence=0.8,
        occurrences=term.occurrences
    )
```

#### ステップ3: 精査

```python
# 問題点保存（run_id不要）
for issue in issues:
    create_issue(
        conn,
        term_name=issue.term,
        issue_type=issue.issue_type,
        description=issue.description
    )
```

#### ステップ4: 改善

```python
# 最終用語集保存（run_id不要）
for term in refined_glossary.terms:
    create_refined_term(
        conn,
        term_name=term.text,
        definition=term.definition,
        confidence=0.9,
        occurrences=term.occurrences
    )
```

### 影響ファイル

- `src/genglossary/cli.py`

## Phase 6: テスト・ドキュメント更新

### テストの更新

#### 既存テストの修正（run_id削除）

- `tests/db/test_document_repository.py`
- `tests/db/test_term_repository.py`
- `tests/db/test_provisional_repository.py`
- `tests/db/test_issue_repository.py`
- `tests/db/test_refined_repository.py`
- `tests/db/conftest.py`: fixture更新

#### 削除するテスト

- `tests/db/test_run_repository.py`

#### 新規テスト

- `tests/db/test_metadata_repository.py`: メタデータCRUD
- `tests/test_cli.py`: generateコマンドのDB保存テスト

### ドキュメントの更新

#### README.md

**更新内容:**
- DB保存がデフォルトになったことを明記
- `--no-db` フラグの説明追加
- `db runs` コマンドを削除
- `regenerate` コマンドの説明追加
- `db info` コマンドの説明追加

**コマンド例の更新:**
```bash
# Before
genglossary generate --input ./target_docs --output ./output/glossary.md --db-path ./genglossary.db

# After
genglossary generate --input ./target_docs --output ./output/glossary.md
# DBは自動的に ./genglossary.db に保存される
```

#### .claude/rules/03-architecture.md

**更新内容:**
- スキーマv2への更新
- `runs` テーブル削除
- `metadata` テーブル追加
- Repository層のAPIドキュメント更新（run_id削除）
- データフロー図の更新
- 新しいCLI構造の反映

**スキーマセクションの更新:**
```markdown
### データベーススキーマ (v2)

...（新スキーマを記載）...
```

**Repository APIセクションの更新:**
```markdown
#### term_repository.py

- `create_term(conn, term_text, category)` - 用語を作成（run_id不要）
- `list_all_terms(conn)` - 全用語を取得
- `delete_all_terms(conn)` - 全用語を削除
...
```

**CLIコマンドセクションの更新:**
```markdown
### DB管理コマンド

genglossary db init              # DB初期化
genglossary db info              # メタデータ表示
genglossary db terms regenerate  # 用語を再抽出
...
```

## Tasks

### Phase 5タスク

- [ ] test_cli.py: generateコマンドのDB保存デフォルト化テスト（TDD）
- [ ] test_cli.py: --no-db フラグのテスト（TDD）
- [ ] cli.py: --db-path デフォルト値を ./genglossary.db に変更
- [ ] cli.py: --no-db フラグ追加
- [ ] cli.py: run_id 関連コード削除
- [ ] cli.py: metadata 更新コード追加
- [ ] テスト実行して成功を確認
- [ ] Phase 5をコミット

### Phase 6タスク

#### テスト更新

- [ ] tests/db/conftest.py: fixture更新（run_id削除）
- [ ] tests/db/test_document_repository.py: run_id削除
- [ ] tests/db/test_term_repository.py: run_id削除、delete_all追加
- [ ] tests/db/test_provisional_repository.py: run_id削除、delete_all追加
- [ ] tests/db/test_issue_repository.py: run_id削除、delete_all追加
- [ ] tests/db/test_refined_repository.py: run_id削除、delete_all追加
- [ ] tests/db/test_run_repository.py: 削除
- [ ] Code simplification review using code-simplifier agent
- [ ] Update .claude/rules/03-architecture.md
- [ ] 全テスト実行して成功を確認

#### ドキュメント更新

- [ ] README.md: DB保存デフォルト化、regenerateコマンド追加
- [ ] .claude/rules/03-architecture.md: スキーマv2、CLI構造更新
- [ ] ドキュメント更新をコミット

### 最終確認

- [ ] Run static analysis (`pyright`)
- [ ] Run all tests (`uv run pytest`)
- [ ] 親チケットのタスクを完了としてマーク
- [ ] Get developer approval

## 検証方法

### Phase 5検証

```bash
# デフォルトでDB保存されることを確認
rm -f ./genglossary.db
uv run genglossary generate --input ./target_docs --output ./output/glossary.md
ls -la ./genglossary.db  # ファイルが作成される

# --no-db でDB保存をスキップ
rm -f ./genglossary.db
uv run genglossary generate --input ./target_docs --output ./output/glossary.md --no-db
ls -la ./genglossary.db  # ファイルが存在しない

# カスタムパスを指定
uv run genglossary generate --input ./target_docs --output ./output/glossary.md --db-path ./custom.db
ls -la ./custom.db  # カスタムパスに作成される

# DB情報確認
uv run genglossary db info
# Output:
# Input Path: ./target_docs
# LLM Provider: ollama
# LLM Model: llama3
# Last Updated: 2026-01-20 02:05:50

# メタデータが正しく保存されていることを確認
python -c "
from genglossary.db import get_connection, get_metadata
conn = get_connection('./genglossary.db')
meta = get_metadata(conn)
print(f'Input: {meta[\"input_path\"]}')
print(f'Provider: {meta[\"llm_provider\"]}')
print(f'Model: {meta[\"llm_model\"]}')
"
```

### Phase 6検証

```bash
# 全テスト実行
uv run pytest -v

# 型チェック
uv run pyright

# ドキュメントの確認
cat README.md | grep -A 10 "regenerate"
cat .claude/rules/03-architecture.md | grep -A 10 "metadata"
```

### 統合テスト

```bash
# 完全なワークフローを確認
rm -f ./genglossary.db

# 1. 初回生成（DB保存）
uv run genglossary generate --input ./target_docs --output ./output/glossary.md

# 2. 用語を手動編集
uv run genglossary db terms list
uv run genglossary db terms update 1 --text "更新後の用語"

# 3. 暫定用語集を再生成
uv run genglossary db provisional regenerate

# 4. 精査を再実行
uv run genglossary db issues regenerate

# 5. 最終用語集を再生成
uv run genglossary db refined regenerate

# 6. Markdownエクスポート
uv run genglossary db refined export-md --output ./output/glossary_updated.md

# 7. 結果確認
cat ./output/glossary_updated.md
```

## Notes

- TDD厳守: テストファースト開発を徹底
- DB保存がデフォルトになることで、ユーザーは常にデータを保持できる
- `--no-db` は軽量実行時やテスト時に使用
- ドキュメントは新しいCLI構造を反映し、わかりやすく記載
- 全ての変更が完了したら、親チケットのタスクを完了としてマーク
