---
priority: 1
tags: [llm, azure, openai, integration]
description: "Add Azure OpenAI Service support as an alternative LLM provider"
created_at: "2026-01-08T14:50:32Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
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
- [ ] openai パッケージを `pyproject.toml` に追加（`uv add openai`）
- [ ] azure-identity パッケージを追加（Azure認証用）

### 2. AzureOpenAIClient の実装（TDDサイクル）
- [ ] テスト作成: `tests/llm/test_azure_openai_client.py` を作成
  - 初期化テスト
  - generate() メソッドのテスト
  - generate_structured() メソッドのテスト
  - エラーハンドリングのテスト
  - リトライロジックのテスト
- [ ] テストを実行して失敗を確認（Red）
- [ ] テストのみをコミット
- [ ] 実装: `src/genglossary/llm/azure_openai_client.py` を作成
  - BaseLLMClient を継承
  - Azure OpenAI SDK を使用
  - エンドポイント、APIキー、デプロイメント名の設定
  - リトライロジックの実装
  - 構造化出力のサポート（JSON mode）
- [ ] テストを実行して成功を確認（Green）
- [ ] 実装をコミット

### 3. 設定管理の拡張
- [ ] config.py に Azure OpenAI 設定を追加
  - AZURE_OPENAI_ENDPOINT
  - AZURE_OPENAI_API_KEY
  - AZURE_OPENAI_DEPLOYMENT_NAME
  - AZURE_OPENAI_API_VERSION
  - LLM_PROVIDER (ollama | azure_openai)
- [ ] 環境変数からの読み込みをサポート
- [ ] デフォルト値の設定

### 4. CLI の更新
- [ ] cli.py で LLM プロバイダーの選択機能を追加
  - `--llm-provider` オプションの追加
  - 設定ファイルからのプロバイダー読み込み
  - プロバイダーに応じたクライアントの初期化

### 5. テストの拡張
- [ ] 統合テストの追加（OllamaとAzure OpenAIの両方）
- [ ] respx を使った HTTP モックテスト
- [ ] エラーケースのテスト

### 6. ドキュメント更新
- [ ] README.md に Azure OpenAI の設定方法を追加
- [ ] `/llm-integration` スキル (SKILL.md) に Azure OpenAI のパターンを追加
- [ ] 環境変数の一覧をドキュメント化

### 7. 最終確認
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [ ] 両方のプロバイダー（Ollama, Azure OpenAI）で動作確認
- [ ] Get developer approval before closing


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
