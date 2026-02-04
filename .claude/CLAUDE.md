# GenGlossary 開発ガイド

**GenGlossary**は、AIを活用してドキュメントから用語集を自動生成するツールです。

## 必須ルール（MUST）

1. **TDD厳守**: テストファースト開発を必ず実施 → `/tdd-workflow` スキルを使用
2. **Git管理**: チケットシステムと連携したワークフロー → `/git-workflow` スキルを使用
3. **開発計画**: コード作成に取りかかる前に `/brainstorming` スキルで計画を明確にする

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

### 詳細ドキュメント（必要時に参照）
- `docs/architecture/` - アーキテクチャガイド（README.md から各詳細へ）

## 困ったときは

- TDDのやり方が分からない → `/tdd-workflow` スキルを使用
- テスト・モックの書き方 → `/testing-strategy` スキルを使用
- コミットメッセージの書き方 → `/git-workflow` スキルを使用
- LLMとの連携方法、プロンプト設計 → `/llm-integration` スキルを使用
- コードスタイル、命名規則 → `/code-style` スキルを使用

## Rules

- Before starting work on a ticket, always read and confirm the ticket details with the user. Don't assume context carries over between sessions.
