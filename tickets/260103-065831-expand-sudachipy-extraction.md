---
priority: 2
tags: [term-extraction, sudachipy, enhancement]
description: "Expand SudachiPy extraction conditions to extract compound nouns and technical terms"
created_at: "2026-01-03T06:58:31Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# Expand SudachiPy Extraction Conditions

## Problem

現在の`MorphologicalAnalyzer`は、SudachiPyで抽出した固有名詞（`pos[0] == "名詞" and pos[1] == "固有名詞"`）のみを用語候補として抽出している。

`analyze-terms`コマンドの実行結果により、以下の問題が明らかになった：

```
■ SudachiPy抽出候補 (19件)
  中央, 代理, 大陸, 近衛, 東, 聖域, 北方, ...

■ LLM承認用語 (0件)
  (なし)

■ 統計
  候補数: 19
  承認率: 0.0% (0/19)
```

**問題点**：
- 一般的な固有名詞（中央、近衛など）のみが抽出され、LLMが承認しない
- 重要な複合語や技術用語が抽出されていない
  - 例: 「アソリウス島騎士団」「魔神代理領」「騎士代理爵位」
- これらの用語は固有名詞タグが付いていないため、現在の実装では抽出されない

## Analysis from sample documents

`examples/case2`の文書から手動で確認した重要用語（現在抽出されていないもの）：

- **組織名**: アソリウス島騎士団、魔神代理領
- **称号・役職**: 騎士代理爵位、近衛騎士団長
- **専門用語**: 聖印、魔神討伐
- **固有名詞の複合語**: ベルリーク・アソリウス、オーラム・インペリウス

これらは品詞タグとして「名詞-普通名詞」や複数形態素の組み合わせで表現されている可能性が高い。

## Proposed Solution

SudachiPyの抽出条件を拡張し、以下を含める：

1. **複合名詞の抽出**
   - 連続する名詞を結合して複合語として抽出
   - 例: 「騎士」+「団」+「長」→「騎士団長」

2. **品詞タグの拡張**
   - 現在: `名詞-固有名詞` のみ
   - 追加候補: `名詞-普通名詞-一般`（文脈依存の専門用語）

3. **フィルタリング条件の追加**
   - 長さフィルタ（3文字以上など）で一般的すぎる語を除外
   - 出現頻度を考慮（複数回出現する語を優先）

## Tasks

- [ ] `MorphologicalAnalyzer`に複合名詞抽出ロジックを追加するテストを作成
- [ ] 複合名詞抽出ロジックを実装
- [ ] 品詞タグ拡張のテストを作成（普通名詞の抽出）
- [ ] 品詞タグ拡張を実装
- [ ] フィルタリング条件（長さ、頻度）のテストを作成
- [ ] フィルタリング条件を実装
- [ ] `examples/case2`で`analyze-terms`を実行し、改善を確認
- [ ] LLM承認率が向上していることを確認（目標: 30%以上）
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing


## Notes

### Implementation Strategy (TDD)

各機能追加はTDDサイクルで実装：
1. テスト作成（期待される抽出結果を定義）
2. テスト失敗確認 → コミット
3. 実装
4. テスト成功確認 → コミット

### Expected Outcome

改善後の`analyze-terms`実行結果（期待値）：

```
■ SudachiPy抽出候補 (40-60件程度)
  アソリウス島騎士団, 魔神代理領, 騎士代理爵位, ベルリーク, ...

■ LLM承認用語 (15-25件程度)
  アソリウス島騎士団, 魔神代理領, 騎士代理爵位, ...

■ 統計
  候補数: 50
  承認率: 40% (20/50)
```

### Reference Files

- 実装対象: `src/genglossary/morphological_analyzer.py:27-40`
- テスト: `tests/test_morphological_analyzer.py`
- 検証用サンプル: `examples/case2/`
