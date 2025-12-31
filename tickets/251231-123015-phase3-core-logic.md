---
priority: 3
tags: [phase3, core-logic, term-extraction, glossary-generation, tdd]
description: "Implement 4-step glossary generation pipeline: extraction, generation, review, and refinement"
created_at: "2025-12-31T12:30:15Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# Phase 3: コアロジックの実装

## 概要

用語集生成の中核となる4つのステップを実装します。各ステップでLLMを活用し、プロンプトエンジニアリングによって高品質な用語集を生成します。

## 実装対象

### 4つのコアコンポーネント
- `src/genglossary/term_extractor.py` - ステップ1: 用語抽出
- `src/genglossary/glossary_generator.py` - ステップ2: 暫定用語集生成
- `src/genglossary/glossary_reviewer.py` - ステップ3: 精査
- `src/genglossary/glossary_refiner.py` - ステップ4: 改善

## Tasks

### TermExtractor - ステップ1（TDDサイクル1）
- [ ] `tests/test_term_extractor.py` 作成
  - LLMクライアントをモック化
  - 期待されるプロンプト形式の検証
  - LLMレスポンスのパーステスト
  - 重複用語の除去テスト
  - 空ドキュメントのハンドリングテスト
- [ ] テスト実行 → 失敗確認
- [ ] コミット（テストのみ）
- [ ] `src/genglossary/term_extractor.py` 実装
  - `TermExtractor` クラス
  - `extract_terms()` メソッド
  - `_create_extraction_prompt()` - プロンプト生成
  - JSON形式でLLMから用語リストを取得
  - 重複除去ロジック
- [ ] テストパス確認
- [ ] コミット（実装）

### GlossaryGenerator - ステップ2（TDDサイクル2）
- [ ] `tests/test_glossary_generator.py` 作成
  - 用語の出現箇所検索テスト（正規表現）
  - コンテキスト抽出テスト
  - 定義生成テスト（LLMモック）
  - 関連用語抽出テスト
  - Glossaryオブジェクト構築テスト
- [ ] テスト実行 → 失敗確認
- [ ] コミット（テストのみ）
- [ ] `src/genglossary/glossary_generator.py` 実装
  - `GlossaryGenerator` クラス
  - `generate()` メソッド
  - `_find_term_occurrences()` - 用語の出現箇所を検索
  - `_generate_definition()` - LLMで定義を生成
  - `_extract_related_terms()` - LLMで関連用語を抽出
  - コンテキスト付きプロンプト設計
- [ ] テストパス確認
- [ ] コミット（実装）

### GlossaryReviewer - ステップ3（TDDサイクル3）
- [ ] `tests/test_glossary_reviewer.py` 作成
  - 用語集全体のレビュープロンプト生成テスト
  - 問題点の抽出テスト
  - GlossaryIssue パーステスト
  - 問題タイプ分類テスト（unclear, contradiction, missing_context）
- [ ] テスト実行 → 失敗確認
- [ ] コミット（テストのみ）
- [ ] `src/genglossary/glossary_reviewer.py` 実装
  - `GlossaryReviewer` クラス
  - `review()` メソッド
  - `_create_review_prompt()` - レビュープロンプト生成
  - `_parse_issues()` - LLMレスポンスから問題リストを抽出
  - 不明点・矛盾の検出ロジック
- [ ] テストパス確認
- [ ] コミット（実装）

### GlossaryRefiner - ステップ4（TDDサイクル4）
- [ ] `tests/test_glossary_refiner.py` 作成
  - 問題解決ロジックテスト
  - 用語定義の更新テスト
  - 関連用語の追加テスト
  - 精錬プロンプト生成テスト
- [ ] テスト実行 → 失敗確認
- [ ] コミット（テストのみ）
- [ ] `src/genglossary/glossary_refiner.py` 実装
  - `GlossaryRefiner` クラス
  - `refine()` メソッド
  - `_resolve_issue()` - 個別問題の解決
  - `_create_refinement_prompt()` - 改善プロンプト生成
  - 追加コンテキストの活用
- [ ] テストパス確認
- [ ] コミット（実装）

### プロンプト最適化
- [ ] 各ステップのプロンプトを検証
- [ ] Few-shot examples の追加検討
- [ ] トークン数の最適化

### 最終確認
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [ ] カバレッジ確認（目標: 80%以上）
- [ ] Get developer approval before closing


## Notes

### プロンプト戦略

**ステップ1: 用語抽出**
```
あなたは技術文書の専門家です。以下のドキュメントから重要な専門用語を抽出してください。

抽出基準:
- ドキュメント内で繰り返し使用される用語
- 特定の文脈で特別な意味を持つ用語
- 読者が理解すべき重要な概念

JSON形式: {"terms": ["用語1", "用語2", ...]}
```

**ステップ2: 定義生成**
```
用語: {term}
出現箇所とコンテキスト: {occurrences_with_context}

このドキュメント固有の使われ方を説明してください。
JSON形式: {"definition": "...", "confidence": 0.0-1.0}
```

**ステップ3: 精査**
```
以下の用語集を精査し、不明確な点や矛盾を特定してください。

チェック観点:
1. 定義が曖昧または不完全な用語
2. 複数の用語間で矛盾する説明
3. 関連用語の欠落
4. 定義が実際の使用例と一致していない箇所

JSON形式: {"issues": [{"term": "...", "issue_type": "...", "description": "..."}]}
```

**ステップ4: 改善**
```
用語: {term}
現在の定義: {current_definition}
問題点: {issue_description}
追加コンテキスト: {additional_context}

改善された定義を提供してください。
JSON形式: {"refined_definition": "...", "related_terms": [...], "confidence": 0.0-1.0}
```

### ファイルパス
- 実装: `/Users/endo5501/Work/GenGlossary/src/genglossary/`
- テスト: `/Users/endo5501/Work/GenGlossary/tests/`

### 参考
- 実装計画: `/Users/endo5501/.claude/plans/frolicking-humming-candy.md`
