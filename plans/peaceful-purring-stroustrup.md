# アーキテクチャドキュメント階層化計画

## 目的

`.claude/rules/03-architecture.md`（約1000行）の自動読み込みによるトークン消費を削減する。

## 変更内容

### 1. ディレクトリ作成

```
docs/                      # 新規作成（自動読み込みされない）
└── architecture.md        # 詳細アーキテクチャ
```

### 2. ファイル移動

| 移動元 | 移動先 |
|--------|--------|
| `.claude/rules/03-architecture.md` | `docs/architecture.md` |

### 3. CLAUDE.md の更新

```diff
 ## ドキュメント構成

 ### 必須ドキュメント
 - [プロジェクト概要](@.claude/rules/00-overview.md) - 4ステップフロー、技術スタック

-### 推奨ドキュメント
-- [アーキテクチャ](@.claude/rules/03-architecture.md) - ディレクトリ構成、データフロー
+### 詳細ドキュメント（必要時に参照）
+- `docs/architecture.md` - ディレクトリ構成、モジュール設計、データフロー
```

## 修正対象ファイル

1. `.claude/rules/03-architecture.md` → `docs/architecture.md` - 移動
2. `.claude/CLAUDE.md` - リンク更新
3. `.claude/rules/00-overview.md:170` - リンク更新
4. `.claude/skills/llm-integration/SKILL.md:630` - リンク更新
5. `.ticket-config.yaml:48` - テンプレートのリンク更新

## 検証方法

1. 新しいClaudeセッションを開始
2. 自動読み込みされるコンテキストから`architecture.md`の内容が消えていることを確認
3. `docs/architecture.md`を明示的に読み込んで内容が保持されていることを確認
