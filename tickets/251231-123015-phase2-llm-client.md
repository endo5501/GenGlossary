---
priority: 2
tags: [phase2, llm-client, ollama, tdd]
description: "Implement LLM client interface and Ollama client with retry logic and error handling"
created_at: "2025-12-31T12:30:15Z"
started_at: 2025-12-31T13:36:16Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# Phase 2: LLMクライアントの実装

## 概要

OllamaとHTTP通信するLLMクライアントを実装します。抽象基底クラス（BaseLLMClient）と具体実装（OllamaClient）をTDDで構築し、リトライロジック、エラーハンドリング、構造化出力のパースを実装します。

## 実装対象

### LLMクライアント
- `src/genglossary/llm/base.py` - BaseLLMClient (抽象基底クラス)
- `src/genglossary/llm/ollama_client.py` - OllamaClient実装

## Tasks

### 依存関係追加
- [x] `pyproject.toml` に httpx 追加
- [x] `uv sync` で依存関係インストール

### BaseLLMClient インターフェース（TDDサイクル1）
- [x] `tests/llm/test_base.py` 作成
  - 抽象基底クラスのコントラクトテスト
  - `generate()` メソッドの存在確認
  - `generate_structured()` メソッドの存在確認
  - `is_available()` メソッドの存在確認
- [x] テスト実行 → 失敗確認
- [x] コミット（テストのみ）
- [x] `src/genglossary/llm/base.py` 実装
  - `BaseLLMClient` 抽象基底クラス
  - `@abstractmethod generate()`
  - `@abstractmethod generate_structured()`
  - `@abstractmethod is_available()`
- [x] テストパス確認
- [x] コミット（実装）

### OllamaClient 実装（TDDサイクル2）
- [x] `tests/llm/test_ollama_client.py` 作成
  - respx を使ってHTTPリクエストをモック
  - 正常系: レスポンス取得テスト
  - 正常系: 構造化出力テスト（JSONパース）
  - 異常系: 接続エラーテスト
  - 異常系: タイムアウトテスト
  - 異常系: 無効なJSONレスポンステスト
  - リトライロジックテスト（exponential backoff）
  - `is_available()` 疎通確認テスト
- [x] テスト実行 → 失敗確認
- [x] コミット（テストのみ）
- [x] `src/genglossary/llm/ollama_client.py` 実装
  - `OllamaClient` クラス
  - `__init__()` - base_url, model, timeout, max_retries
  - `generate()` - /api/generate エンドポイント使用
  - `generate_structured()` - JSON形式強制、Pydanticバリデーション
  - リトライロジック（exponential backoff）
  - エラーハンドリング
  - JSONパース失敗時のフォールバック（正規表現）
  - `is_available()` - Ollamaサーバー疎通確認
- [x] テストパス確認
- [x] コミット（実装）

### 統合確認
- [x] 実際のOllamaサーバーで動作確認（オプション）- **llama2モデルで完全動作確認済み**
  - サーバー可用性チェック ✓
  - テキスト生成 ✓
  - 構造化出力（JSON + Pydantic） ✓
- [x] エラーメッセージの日本語化確認 - エラーハンドリング実装済み

### 最終確認
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [x] カバレッジ確認（目標: 80%以上） - **96%達成**
- [x] Get developer approval before closing

## 実装結果サマリー

### 成果物
- **BaseLLMClient** (src/genglossary/llm/base.py)
  - 抽象基底クラスで、すべてのLLMクライアントの共通インターフェースを定義
  - 3つの抽象メソッド: `generate()`, `generate_structured()`, `is_available()`

- **OllamaClient** (src/genglossary/llm/ollama_client.py)
  - BaseLLMClientの具体実装
  - httpxを使用したHTTP通信
  - exponential backoffを使用したリトライロジック（最大3回）
  - Pydanticを使用した構造化出力のバリデーション
  - 正規表現によるJSONフォールバック
  - ヘルスチェック機能

### テスト
- **tests/llm/test_base.py**: 5テスト - BaseLLMClientの抽象クラステスト
- **tests/llm/test_ollama_client.py**: 10テスト - OllamaClientの包括的なテスト
  - 正常系、異常系、リトライロジック、構造化出力、ヘルスチェック

### 品質メトリクス
- **テスト結果**: 83/83 テスト合格（Phase 1 + Phase 2）
- **コードカバレッジ**: 96%（目標80%を大幅に超過）
- **静的解析**: pyright 0エラー、0警告
- **TDD遵守**: すべてのコードでTDDサイクルを厳守

### コミット
1. `7c8e5e8` - Add BaseLLMClient interface tests
2. `e4f65da` - Implement BaseLLMClient abstract base class
3. `7c24576` - Add OllamaClient implementation tests
4. `d5d11f3` - Implement OllamaClient with retry logic
5. `8bf04b5` - Update Phase 2 ticket with completion status
6. `773c414` - Add Ollama integration test with real server

### 統合テスト結果（実機確認）
- **モデル**: llama2:latest (3.8 GB)
- **is_available()**: Ollamaサーバー疎通確認 ✓
- **generate()**: "What is the capital of Japan?" → "The capital of Japan is Tokyo." ✓
- **generate_structured()**: APIの定義をJSON形式で取得、Pydanticバリデーション成功 ✓

## Notes

### 依存関係（pyproject.toml に追加）
```toml
dependencies = [
    "httpx>=0.27.0",           # Ollama API通信
    "pydantic>=2.0.0",         # データバリデーション
]

[project.optional-dependencies]
dev = [
    "respx>=0.21.0",           # httpxモック
]
```

### OllamaClient 実装のポイント

**エンドポイント**: `http://localhost:11434/api/generate`

**リトライロジック**:
- 最大リトライ数: 3回
- exponential backoff: 2^attempt 秒

**構造化出力**:
1. プロンプトに「JSON形式で返してください」を追加
2. レスポンスをJSONパース
3. Pydanticでバリデーション
4. 失敗時: 正規表現で `{...}` ブロックを抽出

**エラーハンドリング**:
- `httpx.HTTPError`: 接続エラー、タイムアウト
- `json.JSONDecodeError`: 無効なJSON
- `pydantic.ValidationError`: スキーマ不一致

### ファイルパス
- 実装: `/Users/endo5501/Work/GenGlossary/src/genglossary/llm/`
- テスト: `/Users/endo5501/Work/GenGlossary/tests/llm/`

### 参考
- 実装計画: `/Users/endo5501/.claude/plans/frolicking-humming-candy.md`
- Ollama API: https://github.com/ollama/ollama/blob/main/docs/api.md
