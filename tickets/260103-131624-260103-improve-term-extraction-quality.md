---
priority: 1
tags: [term-extraction, sudachipy, llm, quality]
description: "用語抽出の品質向上（包含フィルタ + 2段階LLM分類）"
created_at: "2026-01-03T13:16:24Z"
started_at: 2026-01-03T13:21:09Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# 用語抽出品質向上

## 概要

用語抽出の品質を向上させ、以下を実現する：
- 重複用語（包含関係）の除去
- 重要な固有名詞・組織名の確実な抽出
- 一般名詞の適切な除外

## 背景

### 現状の問題（analyze-term-result.txt）
- **SudachiPy抽出候補**: 3064件
- **LLM承認用語**: 21件（承認率 0.7%）
- **LLM除外用語**: 3043件

### 問題1: SudachiPyの重複抽出
複合名詞抽出が全ての部分組み合わせを生成：
```
入力: "元エデルト軍陸軍士官"
出力: 元エデルト, 元エデルト軍, 元エデルト軍陸軍, 元エデルト軍陸軍士官,
      エデルト軍, エデルト軍陸軍, エデルト軍陸軍士官, 軍陸軍, 軍陸軍士官, 陸軍士官
```

### 問題2: LLMプロンプトの品質
- 3064件を一度に判定させている
- 重要な固有名詞（"エデルト軍"）が除外されている
- 一般名詞（"未亡人", "行方不明"）が承認されている

## アプローチ

**案A+B併用**: 包含フィルタリング + 2段階LLM分類処理

### 処理フロー
```
文書 → [SudachiPy] → 候補用語
              ↓
    [包含関係フィルタリング]  ← Phase 1
              ↓
      [LLM: 分類フェーズ]     ← Phase 2
              ↓
    人名/地名/組織名/役職/技術用語/一般名詞
              ↓
      [LLM: 選別フェーズ]（一般名詞は除外）
              ↓
          承認用語
```

### 分類カテゴリ（6分類）
1. 人名
2. 地名
3. 組織・団体名
4. 役職・称号
5. 技術用語・専門用語
6. 一般名詞（除外対象）

## Tasks

### Phase 1: SudachiPy改善（包含関係フィルタリング）
- [x] `filter_contained_terms()` メソッドのテスト作成
- [x] `filter_contained_terms()` メソッドの実装
- [x] `extract_proper_nouns()` に `filter_contained=True` オプション追加のテスト
- [x] `extract_proper_nouns()` に `filter_contained=True` オプション追加の実装

### Phase 2: 2段階LLM処理
- [x] 分類フェーズ用プロンプト・モデルのテスト作成
- [x] 分類フェーズ用プロンプト・モデルの実装
- [x] 選別フェーズ用プロンプト改善のテスト作成
- [x] 選別フェーズ用プロンプト改善の実装
- [x] `TermExtractor` リファクタリング

### Phase 3: 検証・調整
- [x] `analyze-terms`コマンドで検証（包含フィルタリング結果・分類結果の出力を追加）
- [ ] 結果評価と調整

### 完了条件
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## 成功基準

- [ ] 包含関係にある重複用語が除去される
- [ ] 固有名詞・組織名（"エデルト軍", "アソリウス島騎士団"など）が承認される
- [ ] 一般名詞（"未亡人", "行方不明"など）が除外される

## 修正対象ファイル

| ファイル | 変更内容 |
|---------|---------|
| `src/genglossary/morphological_analyzer.py` | 包含フィルタ追加 |
| `src/genglossary/term_extractor.py` | 2段階LLM処理 |
| `src/genglossary/models/term.py` | カテゴリ分類モデル追加（必要時） |
| `tests/test_morphological_analyzer.py` | 包含フィルタテスト |
| `tests/test_term_extractor.py` | 2段階処理テスト |

## Notes

- 詳細計画: `/Users/endo5501/.claude/plans/cozy-coalescing-gray.md`
