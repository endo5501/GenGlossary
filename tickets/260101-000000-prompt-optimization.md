---
priority: 5
tags: [enhancement, prompt-optimization, llm]
description: "Optimize LLM prompts with few-shot examples and token efficiency"
created_at: "2026-01-01T00:00:00Z"
started_at: 2026-01-13T04:35:22Z
closed_at: null
---

# プロンプト最適化

## 概要

Phase 3で実装した4つのコアコンポーネントのLLMプロンプトを最適化し、より高品質な出力と効率的なトークン使用を実現します。

## 背景

現在のプロンプトは基本的な指示のみで構成されており、以下の改善の余地があります：
- Few-shot examplesによる出力品質の向上
- 不要な説明の削減によるトークン数の最適化

## 実装対象

### Few-shot Examples の追加

各コンポーネントのプロンプトに具体例を追加：

1. **TermExtractor**
   - 良い抽出例と悪い抽出例を提示
   - 適切な粒度の用語選択を示す

2. **GlossaryGenerator**
   - 効果的な定義の例を提示
   - コンテキストの活用方法を示す

3. **GlossaryReviewer**
   - 典型的な問題パターンの例を提示
   - 各issue_typeの具体例を示す

4. **GlossaryRefiner**
   - 改善前後の定義例を提示
   - 問題解決のアプローチを示す

### トークン数の最適化

1. **冗長な説明の削減**
   - 必要最小限の指示に絞る
   - 構造化出力の例を簡潔化

2. **プロンプトテンプレートの見直し**
   - 繰り返しの除去
   - より効率的な表現への置き換え

3. **コンテキスト長の制限**
   - 長すぎるコンテキストの切り詰め
   - 最も重要な情報のみを含める

## Tasks

### Few-shot Examples

- [x] TermExtractorにfew-shot examplesを追加
- [x] GlossaryGeneratorにfew-shot examplesを追加
- [x] GlossaryReviewerにfew-shot examplesを追加
- [x] GlossaryRefinerにfew-shot examplesを追加
- [x] テストでexampleが含まれることを確認（GlossaryReviewer）
- [x] テストでexampleが含まれることを確認（TermExtractor）
- [x] テストでexampleが含まれることを確認（GlossaryGenerator）
- [x] テストでexampleが含まれることを確認（GlossaryRefiner）

### トークン数最適化

- [x] 各プロンプトのトークン数を測定
  - トークン数測定ツールの作成（TDD）
  - TermExtractor、GlossaryGenerator、GlossaryReviewer、GlossaryRefinerのプロンプトを測定
  - ベースラインの記録: TermExtractor: 331トークン, GlossaryGenerator: 199トークン, GlossaryReviewer: 151トークン, GlossaryRefiner: 201トークン, 合計: 882トークン
- [x] 冗長な説明を削減
- [x] プロンプトテンプレートを簡潔化
- [x] コンテキスト長を制限（最大5例など）
- [x] 最適化後のトークン数を測定・比較
  - 最適化後: TermExtractor: 211トークン (-120), GlossaryGenerator: 82トークン (-117), GlossaryReviewer: 151トークン (±0), GlossaryRefiner: 194トークン (-7), 合計: 638トークン (-244, -27.7%)

### 効果測定

- [x] 実際のOllamaで出力品質を評価
  - サンプルドキュメント: target_docs/sample_story.md
  - 最終用語数: 12用語、平均信頼度: 0.88
  - 品質: 高品質な用語集を生成、適切な除外判断
  - 評価結果: quality_evaluation_results.md
- [x] トークン数削減率を計算: 27.7%削減（目標20%を達成）
- [x] レスポンス時間を測定: 合計97.19秒（用語抽出24.39s、生成27.63s、精査29.25s、改善15.90s）

### 最終確認

- [x] すべてのテストがパス (325 passed, 3 xfailed, 1 xpassed)
- [x] pyrightチェックがパス (0 errors, 0 warnings)
- [x] ドキュメント更新
  - prompt_optimization_results.md: 最適化結果の詳細レポート
  - quality_evaluation_results.md: Ollamaでの品質評価レポート
  - scripts/evaluate_quality.py: 品質評価スクリプト

## 成功基準

- Few-shot examplesの追加によりLLM出力の一貫性が向上
- トークン数を20%以上削減
- すべての既存テストが引き続きパス

## 参考

- Phase 3実装: `tickets/done/251231-123015-phase3-core-logic.md`
- プロンプト例: `current-ticket.md` の Notes セクション
