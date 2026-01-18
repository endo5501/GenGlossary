---
priority: 2
tags: [storage, sqlite, cli, performance]
description: "Persist intermediate and final glossary data in SQLite with CLI workflows for update/view."
created_at: "2026-01-18T02:40:04Z"
started_at: 2026-01-18T11:26:39Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# Ticket Overview

現在は最終結果をテキストファイルへ出力するのみで、LLMを使う用語抽出/精査の再実行に時間がかかる。途中データ(機械的抽出語・暫定用語集)と最終用語集をSQLiteへ保存し、繰り返し更新しながら改善できるCLIワークフローを追加する。

## Goals

- 中間データ(機械的抽出語/暫定用語集)と最終用語集をSQLiteへ保存できる
- CLIで「用語リスト」「暫定用語集」「最終用語集」の更新/閲覧ができる
- 既存の4ステップ処理(抽出→生成→精査→改善)を壊さず拡張する

## Scope / Requirements

- `.claude/rules/00-overview.md` と `.claude/rules/03-architecture.md` に沿って設計する
- SQLiteはワンショットではなく、継続的に更新/再利用する前提で設計する
- 既存のMarkdown出力は維持しつつ、DB保存を追加する(移行/互換考慮)
- CLIは `genglossary` のサブコマンドとして追加(例: `genglossary db ...`)

## Tasks

- [ ] 既存のデータフローにDB保存ポイントを定義する(抽出語・暫定用語集・最終用語集)
  - [ ] どのステップがDBの単一トランザクションで完結するか整理
  - [ ] 途中失敗時のロールバック方針を決める
- [x] SQLiteスキーマ設計 ✅
  - [x] `runs`(実行/更新履歴): 入力パス、LLM設定、開始/完了時刻、ステータス
  - [x] `documents`(入力ドキュメント): run_id, file_path, content_hash
  - [x] `terms_extracted`(機械的抽出語): run_id, term_text, category
  - [x] `glossary_provisional`(暫定用語集): run_id, term_name, definition, occurrences(json), confidence
  - [x] `glossary_refined`(最終用語集): run_id, term_name, definition, occurrences(json), confidence
  - [x] `glossary_issues`(精査結果): run_id, term_name, issue_type, description, should_exclude
  - [x] 主要インデックス/外部キー設計 (UNIQUE制約、ON DELETE CASCADE)
  - [x] 再実行時のupsert方針 (UNIQUE制約で実装)
  - [x] migrationsの最低限運用 (schema_versionテーブル、initialize_db関数)
  - [x] JSON保存方針 (serialize_occurrences/deserialize_occurrences実装)
- [x] DBアクセス層(Repository/DAO)を `src/genglossary/db/` に追加 ✅
  - [x] SQLite接続/初期化 (connection.py: Row factory, PRAGMA foreign_keys)
  - [x] schema migrate (schema.py: initialize_db, get_schema_version)
  - [x] run単位でのsave/load API (run_repository.py: 全CRUD実装)
  - [x] 主要CRUD (document/term/provisional/issue/refined_repository.py: 全実装)
  - [x] トランザクション管理 (各repositoryでconn.commit()実装)
- [x] CLIコマンド設計と実装 (完了) ✅
  - [x] `genglossary db init --path ./output/glossary.db`
  - [x] 用語リスト: `genglossary db terms list|import|update|delete`
  - [x] 暫定用語集: `genglossary db provisional list|update|show`
  - [x] 最終用語集: `genglossary db refined list|update|show|export-md`
  - [x] 実行履歴: `genglossary db runs list|show|latest`
  - [x] list/showの出力フォーマット設計 (Rich tableで実装)
  - [x] update/importでの上書きルール定義 (SQL UPDATE文で実装)
  - [x] エラーハンドリング/exit code方針 (try-except, click.Abort実装)
- [x] 既存CLIの出力フローとの整合性を確認(Markdown出力維持) ✅
  - [x] DB保存の有効/無効を設定で切替可能にする案を検討 ✅ (--db-pathオプションで実装)
  - [x] `genglossary generate`コマンドにDB保存機能を統合 (Phase 4) ✅
- [x] テスト追加 ✅
  - [x] スキーマ初期化/CRUDユニットテスト (78テスト: すべてパス)
  - [x] JSON serialize/deserializeテスト (10テスト: すべてパス)
  - [x] CLI主要コマンドの簡易統合テスト (11テスト: すべてパス)
- [x] ドキュメント更新(README or 使い方にDB運用を追記) ✅
  - [x] DB初期化/閲覧/更新コマンド例を追記
  - [x] DBの保存場所と運用方針を追記
  - [x] 全コマンドの使用例をREADME.mdに記載
- [x] Run static analysis (`pyright`) before closing and pass all tests ✅ (0エラー、0警告)
- [x] Run tests (`uv run pytest`) before closing and pass all tests ✅ (414テストすべてパス)
- [ ] Get developer approval before closing

## Notes

- 既存の `output/` へのMarkdown出力は維持し、DB保存はオプション化も検討
- スキーマ/CLIは最小実装で開始し、後から拡張できる形を重視する

## 実装完了状況 (2026-01-18)

### ✅ Phase 1-3 完了 (コア機能)

**実装済みファイル:**
- `src/genglossary/db/schema.py` - スキーマ初期化とマイグレーション
- `src/genglossary/db/connection.py` - 接続管理
- `src/genglossary/db/models.py` - JSONシリアライズ/デシリアライズ
- `src/genglossary/db/run_repository.py` - 実行履歴CRUD
- `src/genglossary/db/document_repository.py` - ドキュメントCRUD
- `src/genglossary/db/term_repository.py` - 抽出語CRUD
- `src/genglossary/db/provisional_repository.py` - 暫定用語集CRUD
- `src/genglossary/db/issue_repository.py` - 精査結果CRUD
- `src/genglossary/db/refined_repository.py` - 最終用語集CRUD
- `src/genglossary/cli_db.py` - DBコマンド群

**利用可能なCLIコマンド:**
```bash
# データベース初期化
genglossary db init [--path ./genglossary.db]

# 実行履歴の確認
genglossary db runs list [--limit 20]
genglossary db runs show <run_id>
genglossary db runs latest
```

**テスト結果:**
- DB/CLIテスト: 89テスト (すべてパス)
- 全体テスト: 414テスト (すべてパス)
- 型チェック: 0エラー、0警告

### ✅ Phase 4 完了 (統合)

**実装完了:**
- [x] `genglossary generate`コマンドに`--db-path`オプションを追加
- [x] 各ステップでのDB保存処理を統合:
  - ドキュメント → documents テーブル
  - 抽出語 → terms_extracted テーブル
  - 暫定用語集 → glossary_provisional テーブル
  - 精査結果 → glossary_issues テーブル
  - 最終用語集 → glossary_refined テーブル
- [x] run status管理 (running → completed/failed)
- [x] エラー時のfail_run呼び出し
- [x] 型チェック: 0エラー ✅
- [x] 全テスト: 414テストすべてパス ✅

**使用例:**
```bash
# DB保存なし（従来通り）
genglossary generate --input ./target_docs --output ./output/glossary.md

# DB保存あり
genglossary generate --input ./target_docs --output ./output/glossary.md --db-path ./genglossary.db
```

### ✅ Phase 5 完了 (CLIコマンド拡張とドキュメント化)

**実装完了 (2026-01-19):**

#### Repository API拡張
- [x] `term_repository.py`: `update_term()`, `delete_term()` 追加
- [x] `provisional_repository.py`: `update_provisional_term()` 追加
- [x] `refined_repository.py`: `update_refined_term()` 追加

#### CLIコマンド実装
**db terms コマンド群:**
- [x] `terms list --run-id <id>`: 用語一覧表示
- [x] `terms show <term_id>`: 用語詳細表示
- [x] `terms update <term_id> --text <text> --category <category>`: 用語更新
- [x] `terms delete <term_id>`: 用語削除
- [x] `terms import --run-id <id> --file <path>`: テキストファイルから用語インポート（1行1用語）

**db provisional コマンド群:**
- [x] `provisional list --run-id <id>`: 暫定用語集一覧表示
- [x] `provisional show <term_id>`: 暫定用語詳細表示
- [x] `provisional update <term_id> --definition <def> --confidence <score>`: 暫定用語更新

**db refined コマンド群:**
- [x] `refined list --run-id <id>`: 最終用語集一覧表示
- [x] `refined show <term_id>`: 最終用語詳細表示
- [x] `refined update <term_id> --definition <def> --confidence <score>`: 最終用語更新
- [x] `refined export-md --run-id <id> --output <path>`: Markdown形式でエクスポート

#### ドキュメント更新
- [x] README.mdに「データベース機能 (SQLite)」セクションを追加
- [x] 全コマンドの使用例を記載
- [x] データベーススキーマの説明を追加

#### テスト結果
- DB/CLIテスト: 109テスト (すべてパス)
- 型チェック (pyright): 0エラー、0警告

**コミット履歴:**
```
001b7c2 Add update_term and delete_term tests
ad0291f Implement update_term and delete_term
7ef04b6 Add update_provisional_term tests
1b2c79d Implement update_provisional_term
9f50407 Add update_refined_term tests
1bd7752 Implement update_refined_term
384f4c2 Add db terms command tests
c59fba8 Implement db terms commands
4a17c53 Add db provisional/refined command tests
39be6d1 Implement db provisional/refined commands
dab0782 Add database commands section to README
```
