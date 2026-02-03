---
priority: 5
tags: [refactoring, code-quality]
description: "除外用語機能のコード簡素化"
created_at: "2026-02-03T18:47:24Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# 除外用語機能のコード簡素化

## 概要

除外用語機能（260203-092010-terms-exclusion-list）のcode-simplifierレビューで指摘された改善点を実装する。

## 改善提案

### 優先度高（即座に適用可能）

#### バックエンド
1. `_process_terms`の簡素化（`dict.fromkeys`使用）
2. `term_extractor.py`のImport文の外部化
3. `add_excluded_term`のRETURNING句使用（SQLite 3.35+確認後）

#### フロントエンド
1. `excludedTermApi`中間レイヤーの削除（直接APIコール）
2. イベントハンドラーのinline最適化

### 優先度中（リファクタリング効果大）

#### バックエンド
1. プロンプト生成ロジックの共通化（`_wrap_and_format_context`抽出）
2. `ExcludedTermResponse`と`ExcludedTerm`モデルの統合検討

#### フロントエンド
1. TermsPageのタブ分割（`TermsTab`/`ExcludedTermsTab`コンポーネント）
2. モーダルコンポーネント抽出（`AddTermModal`）

### 優先度低（アーキテクチャ変更）
1. OpenAPI型定義からTypeScript型の自動生成
2. バリデーションライブラリの統一

## Tasks

- [ ] `_process_terms`を`dict.fromkeys`で簡素化
- [ ] `term_extractor.py`のimport文を関数外に移動
- [ ] `excludedTermApi`中間レイヤーを削除
- [ ] Commit
- [ ] Run tests (`uv run pytest` & `pnpm test`)

## Notes

- 機能的な問題はなく、コード品質改善のためのリファクタリング
- 削減見込み: バックエンド約150-200行、フロントエンド約100-150行
