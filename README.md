# GenGlossary

AIを活用した用語集自動生成ツール

## 概要

GenGlossaryは、ドキュメントから用語を自動抽出し、その文脈に基づいた定義を生成する用語集自動作成ツールです。ローカルで動作するOllamaを使用することで、プライバシーを確保しながら高品質な用語集を生成できます。

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
  -i, --input DIRECTORY  入力ドキュメントのディレクトリ (デフォルト: ./target_docs)
  -o, --output PATH      出力する用語集ファイルのパス (デフォルト: ./output/glossary.md)
  -m, --model TEXT       使用するOllamaモデル名 (デフォルト: dengcao/Qwen3-30B-A3B-Instruct-2507:latest)
  -v, --verbose          詳細ログを表示
  --help                 ヘルプを表示
```

### 使用例

```bash
# 詳細ログ付きで実行
uv run genglossary generate -i ./docs -o ./glossary.md --verbose

# 別のモデルを使用
uv run genglossary generate -m llama3.2
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
# Ollama設定
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=dengcao/Qwen3-30B-A3B-Instruct-2507:latest
OLLAMA_TIMEOUT=60

# 出力設定
DEFAULT_OUTPUT_PATH=./output/glossary.md
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
