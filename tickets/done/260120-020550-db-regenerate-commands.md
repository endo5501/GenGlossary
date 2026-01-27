---
priority: 1
tags: [db, cli, refactoring]
description: "DB更新コマンド強化 - runsテーブル廃止とregenerateコマンド追加"
created_at: "2026-01-20T02:05:50Z"
started_at: 2026-01-20T02:27:06Z # Do not modify manually
closed_at: 2026-01-20T12:13:31Z # Do not modify manually
---

# DB更新コマンド強化計画

## 背景

先日のSQLite対応（ticket: 260118-024004）により、用語集生成の中間データをDBに保存できるようになりました。しかし、現在の設計には以下の課題があります：

- `generate` コマンドのDB保存がオプション（`--db-path`指定時のみ）
- `update` コマンドは1件ずつ手動編集のみ
- 特定のステップだけを再実行してDB更新することができない
- `runs` テーブルによる実行履歴管理が不要な複雑さを生んでいる

## 目標

1. **DB保存を必須化**: `generate` コマンド実行時は常にDBに保存（デフォルト: ./genglossary.db）
2. **再生成コマンドの追加**: `regenerate` サブコマンドで各テーブルをLLM/ファイル読み込みから再生成
3. **スキーマ簡素化**: `runs` テーブルを廃止し、単一データセットのみ管理

## 決定事項

- **コマンド名**: `regenerate` を採用（既存 `update` と明確に区別）
- **DB保存**: デフォルトで必須（./genglossary.db）、`--no-db` フラグで無効化可能
- **runs廃止**: 実行履歴管理をやめ、常に単一データセットを保持（再生成時は上書き）

## コマンド設計

```bash
# 手動編集（既存コマンド維持、--run-id不要に）
genglossary db terms update <term_id> --text "..." --category "..."
genglossary db provisional update <term_id> --definition "..." --confidence 0.9

# 全件再生成（新規コマンド、--run-id不要）
genglossary db terms regenerate --input ./target_docs
genglossary db provisional regenerate --llm-provider ollama --model llama3
genglossary db issues regenerate --llm-provider ollama --model llama3
genglossary db refined regenerate --llm-provider ollama --model llama3
```

## 新しいCLI構造

```
db (group)
├── init                          # DB初期化
├── info                          # メタデータ表示（NEW）
├── terms (group)
│   ├── list                      # 一覧（--run-id不要）
│   ├── show <term_id>
│   ├── update <term_id>
│   ├── delete <term_id>
│   ├── import --file <path>
│   └── regenerate --input <dir>  # NEW
├── provisional (group)
│   ├── list
│   ├── show <term_id>
│   ├── update <term_id>
│   └── regenerate [--llm-provider] [--model]  # NEW
├── issues (group)
│   ├── list                      # NEW
│   └── regenerate [--llm-provider] [--model]  # NEW
└── refined (group)
    ├── list
    ├── show <term_id>
    ├── update <term_id>
    ├── export-md --output <path>
    └── regenerate [--llm-provider] [--model]  # NEW
```

## サブチケット

この計画は以下のサブチケットに分割して実装する：

| サブチケット | 内容 | 依存関係 |
|-------------|------|---------|
| 260120-phase1-schema-repository | Phase 1-2: スキーマ変更 + Repository層更新 | なし |
| 260120-phase2-cli-regenerate | Phase 3-4: CLI更新 + regenerateコマンド | Phase 1-2完了後 |
| 260120-phase3-generate-docs | Phase 5-6: generate必須化 + ドキュメント | Phase 3-4完了後 |

## Tasks

- [x] サブチケット260120-phase1-schema-repositoryの完了
- [x] サブチケット260120-phase2-cli-regenerateの完了
- [x] サブチケット260120-phase3-generate-docsの完了
- [x] 全体の統合テスト実施
- [x] Code simplification review using code-simplifier agent
- [x] Update docs/architecture.md
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing

## 検証方法

### 1. generate コマンドのDB保存必須化

```bash
# デフォルトでDB保存されることを確認
uv run genglossary generate --input ./target_docs --output ./output/glossary.md
ls -la ./genglossary.db  # ファイルが作成される

# --no-db でDB保存をスキップできることを確認
uv run genglossary generate --input ./target_docs --output ./output/glossary.md --no-db

# カスタムパスを指定できることを確認
uv run genglossary generate --input ./target_docs --output ./output/glossary.md --db-path ./custom.db

# DB情報確認
uv run genglossary db info
```

### 2. regenerate コマンド

```bash
# 事前に generate 実行
uv run genglossary generate --input ./target_docs --output ./output/glossary.md

# terms regenerate（用語を再抽出）
uv run genglossary db terms regenerate --input ./target_docs
uv run genglossary db terms list  # 更新された用語を確認

# provisional regenerate (Ollama)
uv run genglossary db provisional regenerate --llm-provider ollama --model llama3
uv run genglossary db provisional list

# provisional regenerate (OpenAI互換API)
uv run genglossary db provisional regenerate \
  --llm-provider openai --openai-base-url http://localhost:8080/v1 --model local-model

# issues regenerate
uv run genglossary db issues regenerate --llm-provider ollama --model llama3
uv run genglossary db issues list

# refined regenerate
uv run genglossary db refined regenerate --llm-provider ollama --model llama3
uv run genglossary db refined list

# 最終結果をMarkdownにエクスポート
uv run genglossary db refined export-md --output ./output/glossary_updated.md
```

### 3. 自動テスト

```bash
# 全テストを実行
uv run pytest

# 型チェック
uv run pyright
```

## Notes

- TDD厳守: 各Phase開始時にまずテストを作成し、失敗を確認してから実装
- 各サブチケット完了後、メインブランチにマージ前にpyright + pytest実行
