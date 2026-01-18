# GenGlossary

AIを活用した用語集自動生成ツール

## 概要

GenGlossaryは、ドキュメントから用語を自動抽出し、その文脈に基づいた定義を生成する用語集自動作成ツールです。ローカルで動作するOllamaに加え、OpenAI、Azure OpenAI、llama.cpp、LM Studioなど、OpenAI互換APIをサポートします。

### 主な機能

- Markdown/テキストファイルからの用語自動抽出
- AIによる文脈に基づいた定義生成
- 用語間の関連性の自動検出
- 用語集の自動精査・改善
- Markdown形式での出力

## インストール

### 前提条件

- Python 3.11以上
- [uv](https://docs.astral.sh/uv/) (パッケージマネージャー)
- [Ollama](https://ollama.ai/) (ローカルLLM)

### セットアップ

```bash
# リポジトリをクローン
git clone https://github.com/yourusername/GenGlossary.git
cd GenGlossary

# 依存関係をインストール
uv sync

# Ollamaのモデルをダウンロード（未取得の場合）
ollama pull dengcao/Qwen3-30B-A3B-Instruct-2507:latest
```

## 使用方法

### 基本的な使い方

```bash
# ドキュメントから用語集を生成
uv run genglossary generate --input ./target_docs --output ./output/glossary.md
```

### オプション

```bash
uv run genglossary generate [OPTIONS]

Options:
  -i, --input DIRECTORY         入力ドキュメントのディレクトリ (デフォルト: ./target_docs)
  -o, --output PATH             出力する用語集ファイルのパス (デフォルト: ./output/glossary.md)
  --llm-provider [ollama|openai]  LLMプロバイダー (デフォルト: ollama)
  -m, --model TEXT              使用するモデル名（プロバイダーごとのデフォルトあり）
  --openai-base-url TEXT        OpenAI互換APIのベースURL
  -v, --verbose                 詳細ログを表示
  --help                        ヘルプを表示
```

### 使用例

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

### 用語抽出の分析（デバッグモード）

用語抽出の品質を確認するため、中間結果を表示できます：

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

## 設定

### 環境変数

`.env`ファイルを作成して環境変数を設定できます：

```bash
# .env.example を参考に .env を作成
cp .env.example .env
```

```env
# LLMプロバイダー選択
LLM_PROVIDER=ollama  # ollama または openai

# Ollama設定
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=dengcao/Qwen3-30B-A3B-Instruct-2507:latest
OLLAMA_TIMEOUT=120

# OpenAI互換API設定
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4o-mini
OPENAI_TIMEOUT=60

# Azure OpenAI設定（オプション）
# AZURE_OPENAI_API_VERSION=2024-02-15-preview

# 出力設定
DEFAULT_OUTPUT_PATH=./output/glossary.md
```

### LLMプロバイダー

GenGlossaryは以下のLLMプロバイダーをサポートします：

#### 1. Ollama（デフォルト）

ローカルで動作するLLMランタイム。プライバシーを確保しながら使用できます。

```bash
# Ollamaのセットアップ
ollama pull dengcao/Qwen3-30B-A3B-Instruct-2507:latest
ollama serve

# 使用
uv run genglossary generate -i ./docs
```

#### 2. OpenAI API

OpenAIの公式API。高品質なGPTモデルを使用できます。

```bash
# 環境変数を設定
export OPENAI_API_KEY=sk-your-api-key-here

# 使用
uv run genglossary generate --llm-provider openai -i ./docs
```

#### 3. Azure OpenAI Service

Azureで提供されるOpenAIサービス。エンタープライズ向け。

```bash
# 環境変数を設定
export OPENAI_BASE_URL=https://your-resource.openai.azure.com
export OPENAI_API_KEY=your-azure-key
export OPENAI_MODEL=your-deployment-name
export AZURE_OPENAI_API_VERSION=2024-02-15-preview

# 使用
uv run genglossary generate --llm-provider openai -i ./docs
```

#### 4. llama.cpp / LM Studio

OpenAI互換モードで動作するローカルLLM。

```bash
# llama.cppサーバーを起動
./llama-server -m model.gguf --port 8080

# 使用
uv run genglossary generate \
  --llm-provider openai \
  --openai-base-url http://localhost:8080/v1 \
  -m local-model \
  -i ./docs
```

### サポートするファイル形式

- Markdown (.md)
- テキスト (.txt)

## 処理フロー

GenGlossaryは以下の4ステップで用語集を生成します：

1. **用語抽出**: ドキュメントを解析し、重要な専門用語を抽出
2. **用語集生成**: 各用語の出現箇所と文脈から暫定的な定義を生成
3. **精査**: 生成された用語集を精査し、不明点や矛盾を検出
4. **改善**: 検出された問題に基づいて定義を改善

## 開発

### テストの実行

```bash
# 全テストを実行
uv run pytest

# カバレッジ付きで実行
uv run pytest --cov=genglossary --cov-report=term-missing

# 特定のテストを実行
uv run pytest tests/test_integration.py -v
```

### 静的解析

```bash
# pyrightで型チェック
uv run pyright
```

### プロジェクト構成

```
GenGlossary/
├── src/genglossary/          # メインパッケージ
│   ├── models/               # データモデル
│   ├── llm/                  # LLMクライアント
│   ├── output/               # 出力フォーマッター
│   ├── document_loader.py    # ドキュメント読み込み
│   ├── term_extractor.py     # 用語抽出
│   ├── glossary_generator.py # 用語集生成
│   ├── glossary_reviewer.py  # 精査
│   ├── glossary_refiner.py   # 改善
│   ├── cli.py               # CLIエントリーポイント
│   └── config.py            # 設定管理
├── tests/                    # テストコード
├── examples/                 # サンプルドキュメント
└── output/                   # 生成された用語集
```

## トラブルシューティング

### Ollamaに接続できない

```
エラー: Ollamaサーバーに接続できません
```

**解決方法:**

1. Ollamaが起動していることを確認:
   ```bash
   ollama serve
   ```

2. 別のターミナルでOllamaが動作していることを確認:
   ```bash
   ollama list
   ```

### OpenAI APIに接続できない

```
エラー: openai APIに接続できません
```

**解決方法:**

1. APIキーが正しく設定されていることを確認:
   ```bash
   echo $OPENAI_API_KEY
   ```

2. ベースURLが正しいことを確認（Azure OpenAIの場合）:
   ```bash
   echo $OPENAI_BASE_URL
   ```

3. ネットワーク接続を確認

4. APIの利用制限やクォータを確認

### モデルが見つからない

```
エラー: モデルが見つかりません
```

**解決方法:**

使用するモデルをダウンロード:
```bash
ollama pull dengcao/Qwen3-30B-A3B-Instruct-2507:latest
```

### JSONパースエラー

LLMの出力が期待した形式でない場合、パースエラーが発生することがあります。
これはモデルの品質に依存します。より高性能なモデルを使用することで改善できます：

```bash
ollama pull llama3.2
uv run genglossary generate -m llama3.2
```

## ライセンス

MIT License

## コントリビューション

1. このリポジトリをフォーク
2. フィーチャーブランチを作成 (`git checkout -b feature/new-feature`)
3. 変更をコミット (`git commit -m 'Add new feature'`)
4. ブランチをプッシュ (`git push origin feature/new-feature`)
5. プルリクエストを作成

## データベース機能 (SQLite)

GenGlossaryは、生成した用語集をSQLiteデータベースに保存し、管理する機能を提供します。

### DB保存付きで用語集生成

```bash
# データベースに保存しながら用語集を生成
uv run genglossary generate -i ./docs -o ./glossary.md --db-path ./genglossary.db
```

### データベースコマンド

#### 初期化

```bash
# データベースを初期化
uv run genglossary db init --path ./genglossary.db
```

#### 実行履歴の管理

```bash
# 実行履歴の一覧を表示
uv run genglossary db runs list

# 最新の実行履歴を表示
uv run genglossary db runs latest

# 特定のRunの詳細を表示
uv run genglossary db runs show 1
```

#### 抽出用語の管理

```bash
# 用語一覧を表示
uv run genglossary db terms list --run-id 1

# 用語詳細を表示
uv run genglossary db terms show 1

# 用語を更新
uv run genglossary db terms update 1 --text "量子計算機" --category "technical"

# 用語を削除
uv run genglossary db terms delete 1

# テキストファイルから用語をインポート（1行1用語）
uv run genglossary db terms import --run-id 1 --file terms.txt
```

#### 暫定用語集の管理

```bash
# 暫定用語集の一覧を表示
uv run genglossary db provisional list --run-id 1

# 暫定用語の詳細を表示
uv run genglossary db provisional show 1

# 暫定用語を更新
uv run genglossary db provisional update 1 --definition "新しい定義" --confidence 0.95
```

#### 最終用語集の管理

```bash
# 最終用語集の一覧を表示
uv run genglossary db refined list --run-id 1

# 最終用語の詳細を表示
uv run genglossary db refined show 1

# 最終用語を更新
uv run genglossary db refined update 1 --definition "新しい定義" --confidence 0.98

# 最終用語集をMarkdown形式でエクスポート
uv run genglossary db refined export-md --run-id 1 --output ./exported.md
```

### データベーススキーマ

GenGlossaryは以下のテーブルを使用します：

- `runs`: 実行履歴
- `documents`: 処理したドキュメント
- `terms_extracted`: 抽出された用語
- `glossary_provisional`: 暫定用語集
- `glossary_refined`: 最終用語集
- `glossary_issues`: 用語集の問題点

