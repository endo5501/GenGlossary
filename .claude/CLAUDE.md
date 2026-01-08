# GenGlossary 開発ガイド

**GenGlossary**は、AIを活用してドキュメントから用語集を自動生成するツールです。

## 必須ルール（MUST）

1. **日本語で会話**: ユーザーとは常に日本語で会話（思考は英語）
2. **TDD厳守**: テストファースト開発を必ず実施 → `/tdd-workflow` スキルを使用
3. **Git管理**: チケットシステムと連携したワークフロー → [詳細](@.claude/rules/02-git-workflow.md)

## クイックスタート

```bash
# 依存関係のインストール
uv sync

# テスト実行
uv run pytest

# チケット一覧
bash scripts/ticket.sh list

# チケット開始
bash scripts/ticket.sh start <ticket-name>

# チケット完了
bash scripts/ticket.sh close
```

## ドキュメント構成

### 必須ドキュメント
- [プロジェクト概要](@.claude/rules/00-overview.md) - 4ステップフロー、技術スタック
- [Gitワークフロー](@.claude/rules/02-git-workflow.md) - ブランチ戦略、コミット規約

### 推奨ドキュメント
- [アーキテクチャ](@.claude/rules/03-architecture.md) - ディレクトリ構成、データフロー
- [LLM統合](@.claude/rules/04-llm-integration.md) - Ollama連携パターン
- [テスト戦略](@.claude/rules/05-testing-strategy.md) - カバレッジ、モック戦略
- [コードスタイル](@.claude/rules/06-code-style.md) - 命名規則、型ヒント

### 具体例集
- [良い/悪いコミット](@.claude/rules/examples/good-bad-commits.md) - コミットメッセージの例
- [モックパターン](@.claude/rules/examples/mock-patterns.md) - respx, MagicMock の活用
- [プロンプト例](@.claude/rules/examples/llm-prompt-examples.md) - LLMプロンプト設計

## 困ったときは

- TDDのやり方が分からない → `/tdd-workflow` スキルを使用
- コミットメッセージの書き方 → [良い例/悪い例](@.claude/rules/examples/good-bad-commits.md)
- モックの書き方 → [モックパターン集](@.claude/rules/examples/mock-patterns.md)
