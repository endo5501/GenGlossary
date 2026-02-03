# CLI使用ガイド

GenGlossaryはコマンドライン（CLI）からも操作できます。このガイドでは、CLIの使い方を説明します。

## 基本的な使い方

```bash
# ドキュメントから用語集を生成
uv run genglossary generate --input ./target_docs --output ./output/glossary.md
```

## オプション

```bash
uv run genglossary generate [OPTIONS]

Options:
  -i, --input DIRECTORY         入力ドキュメントのディレクトリ (デフォルト: ./target_docs)
  -o, --output PATH             出力する用語集ファイルのパス (デフォルト: ./output/glossary.md)
  --llm-provider [ollama|openai]  LLMプロバイダー (デフォルト: ollama)
  -m, --model TEXT              使用するモデル名（プロバイダーごとのデフォルトあり）
  --openai-base-url TEXT        OpenAI互換APIのベースURL
  --db-path PATH                SQLiteデータベースのパス (デフォルト: ./genglossary.db)
  --no-db                       データベース保存をスキップ
  -v, --verbose                 詳細ログを表示
  --help                        ヘルプを表示
```

## 使用例

```bash
# Ollamaで詳細ログ付きで実行
uv run genglossary generate -i ./docs -o ./glossary.md --verbose

# Ollama: 別のモデルを使用
uv run genglossary generate -m llama3.2

# OpenAI APIを使用
uv run genglossary generate --llm-provider openai -m gpt-4o-mini

# Azure OpenAIを使用
uv run genglossary generate --llm-provider openai --openai-base-url https://your-resource.openai.azure.com

# llama.cpp (OpenAI互換モード) を使用
uv run genglossary generate --llm-provider openai --openai-base-url http://localhost:8080/v1 -m local-model
```

## 用語抽出の分析（デバッグモード）

用語抽出の品質を確認するため、中間結果を表示できます。

```bash
# 用語抽出の分析を実行
uv run genglossary analyze-terms --input ./target_docs
```

このコマンドは以下の情報を表示します：

- **SudachiPy抽出候補**: 形態素解析で抽出された固有名詞候補
- **LLM承認用語**: LLMが用語集に含めるべきと判断した用語
- **LLM除外用語**: LLMが除外した用語
- **統計**: 候補数と承認率

**オプション:**

```bash
uv run genglossary analyze-terms [OPTIONS]

Options:
  -i, --input DIRECTORY  入力ドキュメントのディレクトリ（必須）
  -m, --model TEXT       使用するOllamaモデル名
  --help                 ヘルプを表示
```

**使用例:**

```bash
# 用語抽出の品質を確認
uv run genglossary analyze-terms -i ./examples/case2

# 出力例:
# ■ SudachiPy抽出候補 (19件)
#   中央, 代理, 大陸, 近衛, ...
#
# ■ LLM承認用語 (5件)
#   アソリウス島騎士団, 魔神代理領, ...
#
# ■ 統計
#   候補数: 19
#   承認率: 26.3% (5/19)
```

## データベース機能 (SQLite)

GenGlossaryは、生成した用語集をSQLiteデータベースに保存し、管理する機能を提供します。

### DB保存がデフォルト

```bash
# データベースに保存しながら用語集を生成
uv run genglossary generate -i ./docs -o ./glossary.md
# ./genglossary.db に自動保存されます
```

### DB保存をスキップ

```bash
uv run genglossary generate -i ./docs -o ./glossary.md --no-db
```

### カスタムDBパス指定

```bash
uv run genglossary generate -i ./docs -o ./glossary.md --db-path ./custom.db
```

### データベースコマンド

#### 初期化

```bash
# データベースを初期化
uv run genglossary db init --path ./genglossary.db
```

#### メタデータ表示

```bash
uv run genglossary db info
```

#### 抽出用語の管理

```bash
# 用語一覧を表示
uv run genglossary db terms list

# 用語詳細を表示
uv run genglossary db terms show 1

# 用語を更新
uv run genglossary db terms update 1 --text "量子計算機" --category "technical"

# 用語を削除
uv run genglossary db terms delete 1

# テキストファイルから用語をインポート（1行1用語）
uv run genglossary db terms import --file terms.txt
```

#### 再生成コマンド

```bash
# 抽出用語の再生成
uv run genglossary db terms regenerate --input ./target_docs

# 暫定用語集を再生成
uv run genglossary db provisional regenerate

# 精査を再実行
uv run genglossary db issues regenerate

# 最終用語集を再生成
uv run genglossary db refined regenerate
```

#### 暫定用語集の管理

```bash
# 暫定用語集の一覧を表示
uv run genglossary db provisional list

# 暫定用語の詳細を表示
uv run genglossary db provisional show 1

# 暫定用語を更新
uv run genglossary db provisional update 1 --definition "新しい定義" --confidence 0.95
```

#### 最終用語集の管理

```bash
# 最終用語集の一覧を表示
uv run genglossary db refined list

# 最終用語の詳細を表示
uv run genglossary db refined show 1

# 最終用語を更新
uv run genglossary db refined update 1 --definition "新しい定義" --confidence 0.98

# 最終用語集をMarkdown形式でエクスポート
uv run genglossary db refined export-md --output ./exported.md
```

### データベーススキーマ

GenGlossaryは以下のテーブルを使用します：

- `metadata`: 入力パスやLLM設定
- `documents`: 処理したドキュメント
- `terms_extracted`: 抽出された用語
- `glossary_provisional`: 暫定用語集
- `glossary_refined`: 最終用語集
- `glossary_issues`: 用語集の問題点
