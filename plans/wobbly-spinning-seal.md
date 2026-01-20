# SQLite用語集ストレージ - 残りタスク実装プラン

## 概要

チケット `260118-024004-sqlite-glossary-storage` の残りタスクを完了するプラン。

**完了済み**: DB層実装、`generate --db-path`統合、`db init`/`db runs`コマンド
**残り**: CLIコマンド追加（全コマンド実装）、ドキュメント更新、コードレビュー

**選択事項**:
- 実装範囲: 全コマンド（list/show/update/delete/import/export-md）
- インポート形式: 1行1用語のテキストファイル

---

## Phase 1: Repository API拡張 (TDDで実装)

CLIの `update`/`delete` 操作に必要なAPIを追加

### 1.1 term_repository.py
- `update_term(conn, term_id, term_text, category)` - 用語更新
- `delete_term(conn, term_id)` - 用語削除

### 1.2 provisional_repository.py
- `update_provisional_term(conn, term_id, definition, confidence)` - 暫定用語更新

### 1.3 refined_repository.py
- `update_refined_term(conn, term_id, definition, confidence)` - 最終用語更新

**テストファイル**:
- `tests/db/test_term_repository.py`
- `tests/db/test_provisional_repository.py`
- `tests/db/test_refined_repository.py`

---

## Phase 2: CLIコマンド実装

### 2.1 `db terms` コマンド群
```bash
genglossary db terms list --run-id <id>      # 用語一覧
genglossary db terms show <term_id>          # 用語詳細
genglossary db terms import --run-id <id> --file terms.txt  # 1行1用語のテキストからインポート
genglossary db terms update <term_id> --text "新しい用語"
genglossary db terms delete <term_id>
```

**インポートファイル形式** (`terms.txt`):
```
量子コンピュータ
量子ビット
キュービット
重ね合わせ
```

### 2.2 `db provisional` コマンド群
```bash
genglossary db provisional list --run-id <id>   # 暫定用語集一覧
genglossary db provisional show <term_id>       # 用語詳細
genglossary db provisional update <term_id> --definition "新しい定義"
```

### 2.3 `db refined` コマンド群
```bash
genglossary db refined list --run-id <id>       # 最終用語集一覧
genglossary db refined show <term_id>           # 用語詳細
genglossary db refined update <term_id> --definition "新しい定義"
genglossary db refined export-md --run-id <id> --output ./glossary.md
```

**修正ファイル**: `src/genglossary/cli_db.py`
**テストファイル**: `tests/test_cli_db.py`

---

## Phase 3: ドキュメント更新

`README.md` にDBコマンドセクションを追加:

```markdown
## データベース機能 (SQLite)

### DB保存付きで用語集生成
\`\`\`bash
uv run genglossary generate -i ./docs -o ./glossary.md --db-path ./genglossary.db
\`\`\`

### データベースコマンド
\`\`\`bash
# 初期化
genglossary db init --path ./genglossary.db

# 実行履歴
genglossary db runs list
genglossary db runs latest

# 用語リスト
genglossary db terms list --run-id 1

# 最終用語集をエクスポート
genglossary db refined export-md --run-id 1 --output ./exported.md
\`\`\`
```

---

## Phase 4: コードレビュー

`code-simplifier` エージェントで以下をレビュー:
- `src/genglossary/db/` ディレクトリ全体
- `src/genglossary/cli_db.py`

---

## Phase 5: 最終検証

1. `uv run pyright` - 型チェック (0エラー)
2. `uv run pytest` - 全テストパス
3. 実際のDBワークフローを手動テスト:
   ```bash
   genglossary db init --path ./test.db
   genglossary generate -i ./examples/case1 -o ./test.md --db-path ./test.db
   genglossary db runs latest --path ./test.db
   genglossary db refined export-md --run-id 1 --output ./export.md
   ```

---

## 修正対象ファイル一覧

| ファイル | 変更内容 |
|---------|---------|
| `src/genglossary/db/term_repository.py` | update, delete API追加 |
| `src/genglossary/db/provisional_repository.py` | update API追加 |
| `src/genglossary/db/refined_repository.py` | update API追加 |
| `src/genglossary/cli_db.py` | terms/provisional/refinedコマンド追加 |
| `tests/db/test_term_repository.py` | update, deleteテスト追加 |
| `tests/db/test_provisional_repository.py` | updateテスト追加 |
| `tests/db/test_refined_repository.py` | updateテスト追加 |
| `tests/test_cli_db.py` | 新コマンドのテスト追加 |
| `README.md` | DBコマンドセクション追加 |

---

## 検証方法

```bash
# 型チェック
uv run pyright

# テスト
uv run pytest

# 手動動作確認
genglossary db init --path ./test.db
genglossary db terms list --run-id 1
genglossary db refined export-md --run-id 1 --output ./test.md
```
