# アーキテクチャガイド

このドキュメントでは、GenGlossaryプロジェクトの全体構造、ディレクトリ構成、モジュール設計について説明します。

## ドキュメント一覧

| ドキュメント | 説明 |
|------------|------|
| [フロントエンド](./frontend.md) | React SPA、コンポーネント設計、APIクライアント |
| [ディレクトリ構成](./directory-structure.md) | プロジェクトのファイル構造 |
| [モデル・処理・出力](./models.md) | データモデル層、LLMクライアント層、処理レイヤー、出力層 |
| [データベース](./database.md) | データベース層（Schema v4）、Repository パターン、トランザクション管理 |
| [API](./api.md) | FastAPI バックエンド、エンドポイント、スキーマ |
| [Run管理](./runs.md) | バックグラウンドパイプライン実行、スレッディング |
| [CLI](./cli.md) | コマンドラインインターフェース |
| [データフロー](./data-flow.md) | 処理フロー図、カテゴリ分類フロー |
| [設計原則](./design-principles.md) | import規則、モジュール分割、依存関係の原則 |
| [プロンプトセキュリティ](./prompt-security.md) | プロンプトインジェクション防止、エスケープユーティリティ |

## 概要

GenGlossaryは、AIを活用してドキュメントから用語集を自動生成するツールです。

### 4ステップの処理フロー

```
1. 用語抽出 (TermExtractor)
   ↓ ドキュメント → 抽出された用語リスト

2. 用語集生成 (GlossaryGenerator)
   ↓ 用語リスト + ドキュメント → 暫定用語集

3. 精査 (GlossaryReviewer)
   ↓ 暫定用語集 → 問題点のリスト

4. 改善 (GlossaryRefiner)
   ↓ 問題点 + 暫定用語集 → 最終用語集
```

### 主要レイヤー

```
┌─────────────────────────────────────┐
│      フロントエンド層（SPA）        │
│  (React, Mantine, TanStack)         │
├─────────────────────────────────────┤
│          CLI / API 層               │
│  (cli.py, cli_db.py, api/)          │
├─────────────────────────────────────┤
│     処理層        │      DB層       │
│  (Extractor,      │  (repositories, │
│   Generator,      │   schema,       │
│   Reviewer,       │   connection)   │
│   Refiner)        │                 │
├───────────────────┼─────────────────┤
│              LLM層                  │
│    (BaseLLM, OllamaClient)          │
├─────────────────────────────────────┤
│            モデル層                 │
│  (Document, Term, Glossary)         │
└─────────────────────────────────────┘
```

### スキーマバージョン履歴

| バージョン | 主な変更 |
|-----------|---------|
| Schema v1 | 初期スキーマ、`runs`テーブルあり |
| Schema v2 | `runs`テーブル廃止、`metadata`テーブル（単一行）に変更 |
| Schema v3 | `runs`テーブル再導入（バックグラウンド実行管理用、設計変更） |

## クイックリファレンス

### よく参照するドキュメント

- **新機能の実装**: [モデル・処理・出力](./models.md) → [データベース](./database.md) → [API](./api.md) → [フロントエンド](./frontend.md)
- **フロントエンド開発**: [フロントエンド](./frontend.md)
- **API開発**: [API](./api.md)
- **CLI開発**: [CLI](./cli.md)
- **DB変更**: [データベース](./database.md)
- **バックグラウンド処理**: [Run管理](./runs.md)

### 関連ドキュメント

- [プロジェクト概要](/.claude/rules/00-overview.md) - 4ステップフロー、技術スタック
- LLM統合 → `/llm-integration` スキルを使用
- テスト戦略 → `/testing-strategy` スキルを使用
