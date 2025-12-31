---
priority: 2
tags: [phase2, llm-client, ollama, tdd]
description: "Implement LLM client interface and Ollama client with retry logic and error handling"
created_at: "2025-12-31T12:30:15Z"
started_at: null  # Do not modify manually
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
- [ ] `pyproject.toml` に httpx 追加
- [ ] `uv sync` で依存関係インストール

### BaseLLMClient インターフェース（TDDサイクル1）
- [ ] `tests/llm/test_base.py` 作成
  - 抽象基底クラスのコントラクトテスト
  - `generate()` メソッドの存在確認
  - `generate_structured()` メソッドの存在確認
  - `is_available()` メソッドの存在確認
- [ ] テスト実行 → 失敗確認
- [ ] コミット（テストのみ）
- [ ] `src/genglossary/llm/base.py` 実装
  - `BaseLLMClient` 抽象基底クラス
  - `@abstractmethod generate()`
  - `@abstractmethod generate_structured()`
  - `@abstractmethod is_available()`
- [ ] テストパス確認
- [ ] コミット（実装）

### OllamaClient 実装（TDDサイクル2）
- [ ] `tests/llm/test_ollama_client.py` 作成
  - respx を使ってHTTPリクエストをモック
  - 正常系: レスポンス取得テスト
  - 正常系: 構造化出力テスト（JSONパース）
  - 異常系: 接続エラーテスト
  - 異常系: タイムアウトテスト
  - 異常系: 無効なJSONレスポンステスト
  - リトライロジックテスト（exponential backoff）
  - `is_available()` 疎通確認テスト
- [ ] テスト実行 → 失敗確認
- [ ] コミット（テストのみ）
- [ ] `src/genglossary/llm/ollama_client.py` 実装
  - `OllamaClient` クラス
  - `__init__()` - base_url, model, timeout, max_retries
  - `generate()` - /api/generate エンドポイント使用
  - `generate_structured()` - JSON形式強制、Pydanticバリデーション
  - リトライロジック（exponential backoff）
  - エラーハンドリング
  - JSONパース失敗時のフォールバック（正規表現）
  - `is_available()` - Ollamaサーバー疎通確認
- [ ] テストパス確認
- [ ] コミット（実装）

### 統合確認
- [ ] 実際のOllamaサーバーで動作確認（オプション）
- [ ] エラーメッセージの日本語化確認

### 最終確認
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [ ] カバレッジ確認（目標: 80%以上）
- [ ] Get developer approval before closing


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
