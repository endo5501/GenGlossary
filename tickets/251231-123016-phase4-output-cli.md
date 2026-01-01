---
priority: 4
tags: [phase4, output, cli, markdown, tdd]
description: "Implement Markdown output writer, CLI interface, and configuration management"
created_at: "2025-12-31T12:30:16Z"
started_at: 2025-12-31T23:54:26Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# Phase 4: 出力とCLIの実装

## 概要

用語集のMarkdown出力、CLIインターフェース、設定管理を実装します。ユーザーフレンドリーなコマンドライン体験を提供します。

## 実装対象

### 出力とインターフェース
- `src/genglossary/output/markdown_writer.py` - Markdown出力
- `src/genglossary/cli.py` - CLIエントリーポイント
- `src/genglossary/config.py` - 設定管理

## Tasks

### 依存関係追加
- [x] `pyproject.toml` に click, rich, python-dotenv 追加
- [x] `uv sync` で依存関係インストール

### MarkdownWriter（TDDサイクル1）
- [x] `tests/output/test_markdown_writer.py` 作成
  - Markdown形式の生成テスト
  - 用語のフォーマットテスト
  - 出現箇所リンクのテスト
  - 関連用語リンクのテスト
  - ファイル出力テスト
- [x] テスト実行 → 失敗確認
- [x] コミット（テストのみ）
- [x] `src/genglossary/output/markdown_writer.py` 実装
  - `MarkdownWriter` クラス
  - `write()` メソッド
  - `_format_term()` - 用語エントリのフォーマット
  - `_format_occurrences()` - 出現箇所のフォーマット
  - `_format_related_terms()` - 関連用語のリンク
- [x] テストパス確認
- [x] コミット（実装）

### Config管理（TDDサイクル2）
- [x] `tests/test_config.py` 作成
  - 環境変数読み込みテスト
  - 設定ファイル読み込みテスト
  - デフォルト値テスト
  - バリデーションテスト
- [x] テスト実行 → 失敗確認
- [x] コミット（テストのみ）
- [x] `src/genglossary/config.py` 実装
  - `Config` クラス（Pydantic BaseSettings）
  - Ollama設定（base_url, model, timeout）
  - 入出力パス設定
  - 環境変数サポート
- [x] `.env.example` ファイル作成
- [x] テストパス確認
- [x] コミット（実装）

### CLI（TDDサイクル3）
- [x] `tests/test_cli.py` 作成
  - コマンドライン引数パーステスト
  - `generate` コマンドテスト
  - オプション（--input, --output, --model, --verbose）テスト
  - エラーハンドリングテスト
- [x] テスト実行 → 失敗確認
- [x] コミット（テストのみ）
- [x] `src/genglossary/cli.py` 実装
  - `main()` エントリーポイント
  - `generate` コマンド実装
  - rich を使った進捗表示
  - エラーメッセージの日本語化
  - ヘルプメッセージの整備
- [x] `pyproject.toml` に CLI エントリーポイント追加
- [x] `main.py` を CLI のラッパーに更新（pyproject.tomlのエントリーポイントで対応済み）
- [x] テストパス確認
- [x] コミット（実装）

### 動作確認
- [x] `uv run genglossary --help` でヘルプ表示確認
- [x] サンプルドキュメントで実行テスト（プレースホルダー実装確認）
- [x] エラーケース（入力ディレクトリ未存在など）の確認

### 最終確認
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [x] カバレッジ確認（目標: 80%以上） → **95%達成**
- [x] Get developer approval before closing


## Notes

### 依存関係（pyproject.toml に追加）
```toml
dependencies = [
    "click>=8.1.0",            # CLI
    "rich>=13.0.0",            # ターミナル出力
    "python-dotenv>=1.0.0",    # 環境変数
]

[project.scripts]
genglossary = "genglossary.cli:main"
```

### Markdown出力フォーマット

```markdown
# 用語集

生成日時: 2025-12-31 21:30:00
ドキュメント数: 5
モデル: llama3.2

## 用語一覧

### アーキテクチャ

**定義**: システム全体の構造設計を指し、コンポーネント間の関係性と責務の分割を定める概念

**出現箇所**:
- `design.md:15` - "マイクロサービスアーキテクチャを採用する"
- `implementation.md:42` - "アーキテクチャ設計に基づいて実装を進める"

**関連用語**: [コンポーネント](#コンポーネント), [設計パターン](#設計パターン)

---

### コンポーネント

...
```

### CLI設計

```bash
# 基本実行
genglossary generate --input ./target_docs --output ./output/glossary.md

# モデル指定
genglossary generate --model llama3.2

# 詳細ログ
genglossary generate --verbose

# ヘルプ
genglossary --help
genglossary generate --help
```

### .env.example

```env
# Ollama設定
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
OLLAMA_TIMEOUT=120

# 入出力パス
GENGLOSSARY_INPUT_DIR=./target_docs
GENGLOSSARY_OUTPUT_FILE=./output/glossary.md
```

### ファイルパス
- 実装: `/Users/endo5501/Work/GenGlossary/src/genglossary/`
- テスト: `/Users/endo5501/Work/GenGlossary/tests/`
- main.py: `/Users/endo5501/Work/GenGlossary/main.py`

### 参考
- 実装計画: `/Users/endo5501/.claude/plans/frolicking-humming-candy.md`

---

## 完了サマリー

### 実装したコンポーネント
1. **MarkdownWriter** - 用語集のMarkdown出力（14テスト）
2. **Config** - Pydantic Settingsによる設定管理（19テスト）
3. **CLI** - ClickとRichによるCLI（13テスト）

### 品質指標
- ✅ 全テスト: **185個全てパス**
- ✅ カバレッジ: **95%**（目標80%を大幅に上回る）
- ✅ 静的解析: **Pyright 0エラー**
- ✅ TDDサイクル: **3サイクル完遂**（各2コミット）

### コミット履歴
1. `4aad4a0` - Add MarkdownWriter tests for TDD cycle
2. `5df4013` - Implement MarkdownWriter for glossary output
3. `e8da685` - Add Config tests for TDD cycle
4. `6d2239b` - Implement Config management with Pydantic Settings
5. `91c0318` - Add CLI tests for TDD cycle
6. `79d0252` - Implement CLI with Click and Rich
7. `31ebd1c` - Update dependency lock and ticket start time

### 次のステップ
Phase 5: 統合テストとE2E検証で、全コンポーネントを統合して完全な用語集生成パイプラインを構築します。
