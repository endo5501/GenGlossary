# GenGlossary プロジェクトガイド

## プロジェクト概要

**GenGlossary**は、AIを活用してドキュメントから用語集を自動生成するツールです。

### 目的

一般的にドキュメント、小説、資料などには多くの「用語」が使われており、それらの用語は文脈でのみ使われている意味を持つことがあります。このツールは、文章内の単語を抽出し、その文章内での意味を明らかにする用語集を作成することで、文章理解を補助します。

### 4ステップの処理フロー

1. **用語抽出**: ドキュメント内で使用されている単語を抽出
2. **用語集生成**: 暫定的な用語集を作成（依拠する文章の位置を明記）
3. **精査**: 用語集を精査し、不明な点・矛盾している点を列挙
4. **改善**: 列挙された不明点・矛盾点を調査し、用語集をブラッシュアップ

## 技術スタック

### LLM
- **Ollama（ローカル実行）**: http://localhost:11434
- モデル: llama2, llama3.2 など

### 言語とツール
- **Python 3.11+**
- **パッケージ管理**: uv
- **テストフレームワーク**: pytest
- **静的解析**: pyright

### 主要ライブラリ
- httpx: Ollama API通信
- pydantic: データバリデーション、構造化出力
- click: CLI
- rich: ターミナル出力
- pytest, respx: テスト

## 開発方針

### Test-Driven Development (TDD)

**このプロジェクトはTDDで開発します。**

#### TDDサイクル
1. テストを作成
2. テスト実行 → 失敗確認
3. **コミット（テストのみ）**
4. 実装コードを作成
5. テスト実行 → パス確認
6. **コミット（実装）**

#### 重要なルール
- 実装前に必ずテストを書く
- テストが失敗することを確認してからコミット
- テストが通過するまで実装を繰り返す
- 各TDDサイクルで2回コミット（テスト、実装）

### バージョン管理

#### Gitワークフロー
- メインブランチ: `main`
- フィーチャーブランチ: `feature/<ticket-name>`
- コミットメッセージ: 英語で記述

#### チケットシステム
プロジェクトはチケット管理システムを使用します。

**チケット操作**:
```bash
# チケット一覧表示
bash scripts/ticket.sh list

# チケット作業開始
bash scripts/ticket.sh start <ticket-name>

# チケット完了
bash scripts/ticket.sh close
```

**現在のチケット（5つのPhase）**:
1. `251231-123014-phase1-data-models-foundation` - データモデルと基盤
2. `251231-123015-phase2-llm-client` - LLMクライアント
3. `251231-123015-phase3-core-logic` - コアロジック（4ステップ）
4. `251231-123016-phase4-output-cli` - 出力とCLI
5. `251231-123016-phase5-integration-testing` - 統合テストとE2E検証

### パッケージ管理（uv）

```bash
# 依存関係インストール
uv sync

# パッケージ追加
uv add <package-name>

# 開発依存関係追加
uv add --dev <package-name>

# Pythonスクリプト実行
uv run python <script.py>

# pytest実行
uv run pytest

# CLI実行
uv run genglossary --help
```

## アーキテクチャ

### ディレクトリ構成

```
GenGlossary/
├── src/genglossary/              # メインパッケージ
│   ├── models/                   # データモデル
│   │   ├── document.py          # Document, Line管理
│   │   ├── term.py              # Term, TermOccurrence
│   │   └── glossary.py          # Glossary, GlossaryIssue
│   ├── llm/                      # LLMクライアント
│   │   ├── base.py              # BaseLLMClient
│   │   └── ollama_client.py     # OllamaClient
│   ├── document_loader.py        # ドキュメント読み込み
│   ├── term_extractor.py         # ステップ1: 用語抽出
│   ├── glossary_generator.py     # ステップ2: 用語集生成
│   ├── glossary_reviewer.py      # ステップ3: 精査
│   ├── glossary_refiner.py       # ステップ4: 改善
│   ├── output/
│   │   └── markdown_writer.py    # Markdown出力
│   ├── config.py                 # 設定管理
│   └── cli.py                    # CLIエントリーポイント
├── tests/                        # テストコード
├── target_docs/                  # 入力ドキュメント
└── output/                       # 生成された用語集
```

### データフロー

```
DocumentLoader → List[Document]
    ↓
TermExtractor (LLM) → List[str]
    ↓
GlossaryGenerator (LLM) → Glossary (provisional)
    ↓
GlossaryReviewer (LLM) → List[GlossaryIssue]
    ↓
GlossaryRefiner (LLM) → Glossary (refined)
    ↓
MarkdownWriter → output/glossary.md
```

## 重要な技術的決定事項

### Ollama統合

**エンドポイント**: `http://localhost:11434/api/generate`

**リトライロジック**:
- 最大リトライ数: 3回
- exponential backoff: 2^attempt 秒

**構造化出力**:
1. プロンプトに「JSON形式で返してください」を追加
2. レスポンスをJSONパース
3. Pydanticでバリデーション
4. 失敗時: 正規表現で `{...}` ブロックを抽出

### プロンプト戦略

各ステップでLLMに明確な指示を与え、JSON形式で結果を返すように設計しています。

**ステップ1: 用語抽出**
- ドキュメント内で繰り返し使用される用語を抽出
- JSON: `{"terms": ["用語1", "用語2"]}`

**ステップ2: 定義生成**
- 用語の出現箇所とコンテキストから定義を生成
- JSON: `{"definition": "...", "confidence": 0.9}`

**ステップ3: 精査**
- 用語集全体を確認し、不明点・矛盾を検出
- JSON: `{"issues": [{"term": "...", "issue_type": "unclear", "description": "..."}]}`

**ステップ4: 改善**
- 指摘された問題に基づき定義を改善
- JSON: `{"refined_definition": "...", "related_terms": [...]}`

### テスト戦略

**カバレッジ目標**: 80%以上

**モック化**:
- OllamaClient: respx でHTTPリクエストをモック
- DocumentLoader: pytest の tmp_path フィクスチャ
- 各コンポーネント: LLMクライアントを MagicMock で置き換え

**重要なテストケース**:
- ユニットテスト: 各コンポーネントの機能テスト
- 統合テスト: 全パイプラインの連携テスト
- E2Eテスト: 実際のOllamaサーバーを使用した動作確認（オプション）

## 次のステップ

### 実装開始手順

1. **Phase 1チケットを開始**
   ```bash
   bash scripts/ticket.sh start 251231-123014-phase1-data-models-foundation
   ```

2. **依存関係のインストール**
   ```bash
   uv sync
   ```

3. **プロジェクト構造の作成**
   ```bash
   mkdir -p src/genglossary/{models,llm,output}
   mkdir -p tests/{models,llm,output}
   mkdir -p target_docs output
   ```

4. **TDDサイクル開始**
   - `tests/models/test_document.py` 作成
   - テスト実行 → 失敗確認 → コミット
   - `src/genglossary/models/document.py` 実装
   - テストパス → コミット

5. **各Phaseを順番に実装**
   - Phase 1: データモデルと基盤
   - Phase 2: LLMクライアント
   - Phase 3: コアロジック
   - Phase 4: 出力とCLI
   - Phase 5: 統合テストとE2E検証

### 完了条件

各Phaseの完了条件:
- [ ] すべてのテストがパス（`uv run pytest`）
- [ ] 静的解析がパス（`pyright`）
- [ ] カバレッジ 80%以上
- [ ] 開発者承認

## 参考資料

- **実装計画**: `/Users/endo5501/.claude/plans/frolicking-humming-candy.md`
- **チケット**: `/Users/endo5501/Work/GenGlossary/tickets/`
- **Ollama API**: https://github.com/ollama/ollama/blob/main/docs/api.md
- **プロジェクト仕様**: `/Users/endo5501/Work/GenGlossary/plan.md`

## 開発時の注意事項

### TDDを厳守する
- テストファーストを常に意識
- 実装前にテストを書く
- コミットは2回（テスト、実装）

### コミットメッセージ
- 英語で記述
- 明確で簡潔に
- 例: "Add Document model tests", "Implement Document model"

### プロンプト改善
- LLMの出力品質が低い場合、プロンプトを改善
- Few-shot examples の追加を検討
- トークン数の最適化

### Ollamaの準備
- Phase 2以降では実際のOllamaサーバーが必要
- `ollama serve` でサーバー起動
- モデルのダウンロード: `ollama pull llama2`
