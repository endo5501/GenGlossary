---
priority: 1
tags: [phase1, data-models, foundation, tdd]
description: "Implement data models (Document, Term, Glossary) and DocumentLoader following TDD workflow"
created_at: "2025-12-31T12:30:14Z"
started_at: 2025-12-31T12:40:44Z # Do not modify manually
closed_at: 2025-12-31T13:01:06Z # Do not modify manually
---

# Phase 1: データモデルと基盤の実装

## 概要

GenGlossaryの基礎となるデータモデルとドキュメント読み込み機能を実装します。すべてTDDワークフロー（テスト作成→失敗確認→コミット→実装→テストパス→コミット）に従って進めます。

## 実装対象

### データモデル
- `src/genglossary/models/document.py` - Document, Line管理
- `src/genglossary/models/term.py` - Term, TermOccurrence
- `src/genglossary/models/glossary.py` - Glossary, GlossaryIssue

### ユーティリティ
- `src/genglossary/document_loader.py` - ドキュメント読み込み

## Tasks

### 準備
- [x] プロジェクト構造作成: `src/genglossary/`, `tests/`, `target_docs/`, `output/`
- [x] `pyproject.toml` 更新（依存関係追加）
- [x] `uv sync` で依存関係インストール

### Document モデル（TDDサイクル1）
- [x] `tests/models/test_document.py` 作成
  - ファイル読み込みテスト
  - 行取得テスト
  - コンテキスト取得テスト
- [x] テスト実行 → 失敗確認
- [x] コミット（テストのみ）
- [x] `src/genglossary/models/document.py` 実装
  - `Document` dataclass
  - `get_line()` メソッド
  - `get_context()` メソッド
- [x] テストパス確認
- [x] コミット（実装）

### Term モデル（TDDサイクル2）
- [x] `tests/models/test_term.py` 作成
  - TermOccurrence 作成テスト
  - Term 作成テスト
  - 関連用語リンクテスト
- [x] テスト実行 → 失敗確認
- [x] コミット（テストのみ）
- [x] `src/genglossary/models/term.py` 実装
  - `TermOccurrence` dataclass
  - `Term` dataclass
- [x] テストパス確認
- [x] コミット（実装）

### Glossary モデル（TDDサイクル3）
- [x] `tests/models/test_glossary.py` 作成
  - GlossaryIssue 作成テスト
  - Glossary 作成テスト
  - 用語の追加・検索テスト
- [x] テスト実行 → 失敗確認
- [x] コミット（テストのみ）
- [x] `src/genglossary/models/glossary.py` 実装
  - `GlossaryIssue` dataclass
  - `Glossary` dataclass
- [x] テストパス確認
- [x] コミット（実装）

### DocumentLoader（TDDサイクル4）
- [x] `tests/test_document_loader.py` 作成
  - ファイル検索テスト（.txt, .md）
  - ディレクトリ読み込みテスト
  - エラーハンドリングテスト
- [x] テスト実行 → 失敗確認
- [x] コミット（テストのみ）
- [x] `src/genglossary/document_loader.py` 実装
  - `DocumentLoader` クラス
  - `load_documents()` メソッド
- [x] テストパス確認
- [x] コミット（実装）

### 最終確認
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [x] カバレッジ確認（目標: 80%以上） → 99%達成
- [x] Get developer approval before closing


## Notes

### 依存関係（pyproject.toml に追加）
```toml
dependencies = [
    "pydantic>=2.0.0",         # データバリデーション
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.12.0",
]
```

### データモデル設計のポイント
- `Document`: ファイルパス、内容、行配列を保持
- `TermOccurrence`: 用語の出現箇所（行番号、前後のコンテキスト）
- `Term`: 用語名、定義、出現箇所リスト、関連用語、確信度
- `Glossary`: 用語辞書、問題リスト、メタデータ

### ファイルパス
- 実装: `/Users/endo5501/Work/GenGlossary/src/genglossary/models/`
- テスト: `/Users/endo5501/Work/GenGlossary/tests/models/`

### 参考
- 実装計画: `/Users/endo5501/.claude/plans/frolicking-humming-candy.md`
