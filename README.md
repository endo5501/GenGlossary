# GenGlossary

AIを活用した用語集自動生成ツール

## 概要

GenGlossaryは、ドキュメントから用語を自動抽出し、その文脈に基づいた定義を生成する用語集自動作成ツールです。Webブラウザから操作できるGUIを提供し、直感的な操作で用語集を作成・管理できます。

### 主な機能

- Markdown/テキストファイルからの用語自動抽出
- AIによる文脈に基づいた定義生成
- 用語間の関連性の自動検出
- 用語集の自動精査・改善
- Webブラウザから操作できるGUI
- Markdown形式での出力

### 対応LLM

ローカルで動作するOllamaに加え、OpenAI、Azure OpenAI、llama.cpp、LM Studioなど、OpenAI互換APIをサポートします。

## クイックスタート

### 前提条件

- Python 3.11以上
- Node.js 18以上
- [uv](https://docs.astral.sh/uv/) (パッケージマネージャー)
- [Ollama](https://ollama.ai/) (ローカルLLM)

### セットアップ

```bash
# リポジトリをクローン
git clone https://github.com/yourusername/GenGlossary.git
cd GenGlossary

# バックエンドの依存関係をインストール
uv sync

# フロントエンドの依存関係をインストール
cd frontend
npm install
cd ..

# Ollamaのモデルをダウンロード（未取得の場合）
ollama pull dengcao/Qwen3-30B-A3B-Instruct-2507:latest
```

### 起動方法

**ターミナル1: バックエンドサーバーを起動**

```bash
uv run genglossary api serve --reload
```

**ターミナル2: フロントエンドを起動**

```bash
cd frontend
npm run dev
```

ブラウザで http://localhost:5173 を開くとWeb UIにアクセスできます。

## Web UIの使い方

### プロジェクト一覧（ホーム画面）

- **プロジェクト一覧**: 名前、最終更新日時、ドキュメント数、用語数を表示
- **プロジェクト概要カード**: 選択したプロジェクトの詳細と操作ボタン（開く/複製/削除）
- **新規作成**: プロジェクト名とLLM設定を指定して作成

### プロジェクト詳細画面

左サイドバーから各機能にアクセスできます：

| ページ | 説明 |
|-------|------|
| **Files** | 登録ドキュメントの一覧表示、ファイル追加、差分スキャン |
| **Terms** | 抽出された用語の一覧・詳細表示、再抽出、手動追加/削除 |
| **Provisional** | 暫定用語集の一覧・編集（定義、confidence調整） |
| **Issues** | 精査結果の一覧（タイプ別フィルタ対応）、再精査 |
| **Refined** | 最終用語集の一覧・詳細表示、Markdownエクスポート |
| **Document Viewer** | 原文ドキュメントの閲覧 |
| **Settings** | プロジェクト名、LLM設定の編集 |

### グローバル操作バー

画面上部に以下の操作を配置：

- **Run ボタン**: パイプライン実行（用語抽出→用語集生成→精査→改善）
- **Stop ボタン**: 実行中のパイプラインをキャンセル
- **実行状態**: 現在の状態（Up-to-date / Running / Failed など）を表示

### ログパネル

画面下部に折りたたみ可能なログビューアを配置。パイプライン実行中のログをリアルタイムで確認できます。

### キーボード操作

各ページのリスト項目はキーボードで操作できます：

- **Tab**: 項目間を移動
- **Enter / Space**: 項目を選択

## 処理フロー

GenGlossaryは以下の4ステップで用語集を生成します：

1. **用語抽出**: ドキュメントを解析し、重要な専門用語を抽出
2. **用語集生成**: 各用語の出現箇所と文脈から暫定的な定義を生成
3. **精査**: 生成された用語集を精査し、不明点や矛盾を検出
4. **改善**: 検出された問題に基づいて定義を改善

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

# フロントエンド設定（frontend/.envに配置）
# VITE_API_BASE_URL=http://localhost:8000
```

### LLMプロバイダー

GenGlossaryは以下のLLMプロバイダーをサポートします：

#### 1. Ollama（デフォルト）

ローカルで動作するLLMランタイム。プライバシーを確保しながら使用できます。

```bash
# Ollamaのセットアップ
ollama pull dengcao/Qwen3-30B-A3B-Instruct-2507:latest
ollama serve
```

#### 2. OpenAI API

OpenAIの公式API。高品質なGPTモデルを使用できます。

```bash
# 環境変数を設定
export OPENAI_API_KEY=sk-your-api-key-here
```

#### 3. Azure OpenAI Service

Azureで提供されるOpenAIサービス。エンタープライズ向け。

```bash
# 環境変数を設定
export OPENAI_BASE_URL=https://your-resource.openai.azure.com
export OPENAI_API_KEY=your-azure-key
export OPENAI_MODEL=your-deployment-name
export AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

#### 4. llama.cpp / LM Studio

OpenAI互換モードで動作するローカルLLM。

```bash
# llama.cppサーバーを起動
./llama-server -m model.gguf --port 8080
```

### サポートするファイル形式

- Markdown (.md)
- テキスト (.txt)

## CLI（コマンドライン）

GenGlossaryはコマンドラインからも操作できます。詳細は [CLI使用ガイド](docs/cli-usage.md) を参照してください。

```bash
# 基本的な使い方
uv run genglossary generate --input ./target_docs --output ./output/glossary.md
```

## 開発

### Git hooks のセットアップ

コミット前に TypeScript の型チェックを自動実行するため、以下のコマンドで Git hooks を設定してください：

```bash
git config core.hooksPath .husky
```

これにより、コミット時に `pnpm run typecheck` が実行され、型エラーがあるとコミットがブロックされます。

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

### フロントエンド開発

```bash
cd frontend

# 開発サーバー起動
npm run dev

# テスト実行
npm test

# プロダクションビルド
npm run build

# リント
npm run lint
```

### プロジェクト構成

```
GenGlossary/
├── src/genglossary/          # メインパッケージ
│   ├── api/                  # FastAPI バックエンド
│   │   ├── main.py           # APIエントリーポイント
│   │   ├── routers/          # APIルーター
│   │   └── schemas.py        # Pydanticスキーマ
│   ├── models/               # データモデル
│   ├── llm/                  # LLMクライアント
│   ├── output/               # 出力フォーマッター
│   ├── storage/              # データベースアクセス層
│   ├── document_loader.py    # ドキュメント読み込み
│   ├── term_extractor.py     # 用語抽出
│   ├── glossary_generator.py # 用語集生成
│   ├── glossary_reviewer.py  # 精査
│   ├── glossary_refiner.py   # 改善
│   ├── cli.py               # CLIエントリーポイント
│   └── config.py            # 設定管理
├── frontend/                 # React フロントエンド
│   ├── src/
│   │   ├── api/              # APIクライアント・フック
│   │   ├── components/       # Reactコンポーネント
│   │   ├── pages/            # ページコンポーネント
│   │   └── routes/           # ルーティング設定
│   └── package.json
├── tests/                    # バックエンドテストコード
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
```

## ライセンス

MIT License

## コントリビューション

1. このリポジトリをフォーク
2. フィーチャーブランチを作成 (`git checkout -b feature/new-feature`)
3. 変更をコミット (`git commit -m 'Add new feature'`)
4. ブランチをプッシュ (`git push origin feature/new-feature`)
5. プルリクエストを作成
