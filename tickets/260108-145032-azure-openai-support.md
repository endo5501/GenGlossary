---
priority: 1
tags: [llm, azure, openai, integration]
description: "Add Azure OpenAI Service support as an alternative LLM provider"
created_at: "2026-01-08T14:50:32Z"
started_at: 2026-01-13T00:03:36Z # Do not modify manually
closed_at: 2026-01-13T04:33:55Z # Do not modify manually
---

# Ticket Overview

現在、GenGlossaryはOllamaのみをLLMプロバイダーとしてサポートしています。
Azure OpenAI Serviceにも対応できるよう拡張し、会社のAzure OpenAI Serviceに接続して使用できるようにします。

## 目標

- BaseLLMClientインターフェースを実装したAzureOpenAIClientクラスの追加
- TDD（テスト駆動開発）に従った実装
- Ollamaとの互換性を維持
- 設定ファイルまたは環境変数でプロバイダーを切り替え可能に

## Tasks

### 1. 依存関係の追加
- [x] ~~openai パッケージを `pyproject.toml` に追加（`uv add openai`）~~
  - **実装方針変更**: 既存のhttpxを使用（軽量、互換性向上のため）
- [x] ~~azure-identity パッケージを追加（Azure認証用）~~
  - **実装方針変更**: API Key認証のみ実装

### 2. OpenAICompatibleClient の実装（TDDサイクル）
- [x] テスト作成: `tests/llm/test_openai_compatible_client.py` を作成
  - 初期化テスト
  - generate() メソッドのテスト（OpenAI, Azure）
  - generate_structured() メソッドのテスト（JSON mode）
  - エラーハンドリングのテスト（429, 401, 5xx）
  - リトライロジックのテスト
  - Azure API version パラメータのテスト
  - 合計20テストケース
- [x] テストを実行して失敗を確認（Red）
- [x] テストのみをコミット
- [x] 実装: `src/genglossary/llm/openai_compatible_client.py` を作成
  - BaseLLMClient を継承
  - httpx を使用（OpenAI SDK不使用）
  - OpenAI, Azure OpenAI, llama.cpp, LM Studio 対応
  - 認証ヘッダーの自動切り替え（Azure vs OpenAI）
  - 指数バックオフによるリトライロジック
  - 構造化出力のサポート（JSON mode + Pydantic）
- [x] テストを実行して成功を確認（Green）
- [x] 実装をコミット

### 3. 設定管理の拡張
- [x] config.py に OpenAI互換API 設定を追加
  - LLM_PROVIDER (ollama | openai)
  - OPENAI_BASE_URL
  - OPENAI_API_KEY
  - OPENAI_MODEL
  - OPENAI_TIMEOUT
  - AZURE_OPENAI_API_VERSION
- [x] 環境変数からの読み込みをサポート
- [x] デフォルト値の設定
- [x] プロバイダーのバリデーション

### 4. CLI の更新
- [x] cli.py で LLM プロバイダーの選択機能を追加
  - `--llm-provider` オプションの追加（ollama | openai）
  - `--openai-base-url` オプションの追加
  - create_llm_client() ファクトリ関数の実装
  - generate, analyze-terms コマンドでの対応

### 5. テストの拡張
- [x] OpenAI互換クライアントの包括的テスト（20ケース）
- [x] respx を使った HTTP モックテスト
- [x] エラーケースのテスト（429, 401, 5xx）
- [x] Azure固有のテスト（api-version パラメータ）

### 6. ドキュメント更新
- [x] README.md に OpenAI互換API の設定方法を追加
  - OpenAI, Azure OpenAI, llama.cpp の設定例
  - 環境変数一覧
  - トラブルシューティング
- [x] `/llm-integration` スキル (SKILL.md) に OpenAI互換パターンを追加
  - 認証ヘッダーの違い
  - JSON mode の使い方
  - リトライ戦略

### 7. コードレビューとリファクタリング
- [x] code-simplifier エージェントによるレビュー
- [x] 共通メソッドの base.py への抽出
  - _build_json_prompt()
  - _parse_json_response()
  - _retry_json_parsing()
- [x] OllamaClient, OpenAICompatibleClient の簡素化
- [x] cli.py の create_llm_client() 簡素化

### 8. 最終確認
- [x] Run static analysis (`pyright`) - 0 errors
- [x] Run tests (`uv run pytest`) - 314 passed
- [x] すべてのコミット完了
- [x] Get developer approval before closing


## Notes

### Azure OpenAI の認証方法
- API Key 認証を使用
- 将来的には Azure AD 認証も検討

### 構造化出力のサポート
- Azure OpenAI の JSON mode (`response_format={"type": "json_object"}`) を使用
- Pydantic モデルとの統合

### リトライロジック
- OllamaClient と同様の指数バックオフを実装
- Azure OpenAI 固有のエラー（RateLimitError, ServiceUnavailableError）に対応

### 参考資料
- Azure OpenAI Service ドキュメント: https://learn.microsoft.com/azure/ai-services/openai/
- openai Python SDK: https://github.com/openai/openai-python

### 既存コードとの互換性
- BaseLLMClient インターフェースを厳守
- 既存の TermExtractor, GlossaryGenerator などは変更不要
