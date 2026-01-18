---
priority: 2
tags: [storage, sqlite, cli, performance]
description: "Persist intermediate and final glossary data in SQLite with CLI workflows for update/view."
created_at: "2026-01-18T02:40:04Z"
started_at: null  # Do not modify manually
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
- [ ] SQLiteスキーマ設計
  - [ ] `runs`(実行/更新履歴): 入力パス、LLM設定、開始/完了時刻、ステータス
  - [ ] `documents`(入力ドキュメント): run_id, file_path, content_hash, created_at
  - [ ] `terms_extracted`(機械的抽出語): run_id, term_text, source, created_at
  - [ ] `glossary_provisional`(暫定用語集): run_id, term_text, definition, occurrences(json), created_at
  - [ ] `glossary_refined`(最終用語集): run_id, term_text, definition, occurrences(json), created_at
  - [ ] `glossary_issues`(精査結果): run_id, term_text, issue_type, description
  - [ ] 主要インデックス/外部キー設計
  - [ ] 再実行時のupsert方針(同一runの再書込/最新版更新)
  - [ ] migrationsの最低限運用(テーブル作成/バージョン管理)
  - [ ] JSON保存方針(occurrences/metadataのserialize/deserialize)
- [ ] DBアクセス層(Repository/DAO)を `src/genglossary/` に追加
  - [ ] SQLite接続/初期化(接続パス、PRAGMA設定)
  - [ ] schema migrate(最小限)の実装
  - [ ] run単位でのsave/load API
  - [ ] 主要CRUD(terms/provisional/refined/issues)の薄いAPI
  - [ ] トランザクション管理(一括保存/更新)
- [ ] CLIコマンド設計と実装
  - [ ] `genglossary db init --path ./output/glossary.db`
  - [ ] 用語リスト: `genglossary db terms list|import|update|delete`
  - [ ] 暫定用語集: `genglossary db provisional list|update|show`
  - [ ] 最終用語集: `genglossary db refined list|update|show|export-md`
  - [ ] 実行履歴: `genglossary db runs list|show|latest`
  - [ ] list/showの出力フォーマット設計(テーブル/JSON/Markdown)
  - [ ] update/importでの上書きルール定義(同名termの扱い)
  - [ ] エラーハンドリング/exit code方針
- [ ] 既存CLIの出力フローとの整合性を確認(Markdown出力維持)
  - [ ] DB保存の有効/無効を設定で切替可能にする案を検討
- [ ] テスト追加
  - [ ] スキーマ初期化/CRUDユニットテスト
  - [ ] JSON serialize/deserializeテスト
  - [ ] CLI主要コマンドの簡易統合テスト
- [ ] ドキュメント更新(README or 使い方にDB運用を追記)
  - [ ] DB初期化/閲覧/更新コマンド例を追記
  - [ ] DBの保存場所と運用方針を追記
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## Notes

- 既存の `output/` へのMarkdown出力は維持し、DB保存はオプション化も検討
- スキーマ/CLIは最小実装で開始し、後から拡張できる形を重視する
