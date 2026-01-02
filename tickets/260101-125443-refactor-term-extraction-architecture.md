---
priority: 1
tags: [refactor, term-extraction, sudachipy]
description: "用語抽出アーキテクチャを刷新 - SudachiPy形態素解析 + LLM判定方式に変更"
created_at: "2026-01-01T12:54:43Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# 用語抽出アーキテクチャ刷新

## 概要

用語抽出処理を根本的に改善する。LLMに直接抽出させるのではなく、形態素解析で固有名詞を切り出し、LLMで用語集への採用を判定する。

### 現在の問題
- LLMが「ゆっくり休みなさい」「クソ不味い」など文やフレーズを用語として抽出
- 辞書的フィルタリングでは対応しきれない
- 関連用語機能が正常に動作していない

### 新しいアプローチ
```
ドキュメント → [SudachiPy] 固有名詞抽出 → [LLM] 用語判定 → 用語リスト
```

## Tasks

### Step 1: 関連用語機能の削除
- [ ] テスト修正（関連用語テストを削除）
- [ ] `uv run pytest` → 失敗確認
- [ ] コミット: "Remove related terms tests"
- [ ] 実装修正（models, generator, refiner, writer）
- [ ] `uv run pytest` → パス確認
- [ ] コミット: "Remove related terms feature"

### Step 2: SudachiPy依存追加
- [ ] `uv add sudachipy sudachidict_core`
- [ ] コミット: "Add SudachiPy dependencies"

### Step 3: MorphologicalAnalyzer実装
- [ ] `tests/test_morphological_analyzer.py` 作成
- [ ] `uv run pytest tests/test_morphological_analyzer.py` → 失敗確認
- [ ] コミット: "Add MorphologicalAnalyzer tests"
- [ ] `src/genglossary/morphological_analyzer.py` 実装
- [ ] `uv run pytest tests/test_morphological_analyzer.py` → パス確認
- [ ] コミット: "Implement MorphologicalAnalyzer with SudachiPy"

### Step 4: TermExtractor刷新
- [ ] `tests/test_term_extractor.py` 書き換え（古いフィルタテスト削除）
- [ ] `uv run pytest tests/test_term_extractor.py` → 失敗確認
- [ ] コミット: "Update TermExtractor tests for new architecture"
- [ ] `src/genglossary/term_extractor.py` 刷新
- [ ] `uv run pytest tests/test_term_extractor.py` → パス確認
- [ ] コミット: "Refactor TermExtractor to use SudachiPy and LLM judgment"

### Step 5: 統合テスト更新
- [ ] `tests/test_integration.py`, `tests/conftest.py` 更新
- [ ] `uv run pytest` → 全テストパス確認
- [ ] コミット: "Update integration tests"

### Step 6: 動作確認
- [ ] `uv run genglossary generate --input tmp/example2 --output tmp/test_output.md`
- [ ] 抽出結果を検証

### 完了条件
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## 修正対象ファイル

### 新規作成
| ファイル | 内容 |
|---------|------|
| `src/genglossary/morphological_analyzer.py` | SudachiPyラッパー |
| `tests/test_morphological_analyzer.py` | 形態素解析テスト |

### 大幅修正
| ファイル | 変更内容 |
|---------|---------|
| `src/genglossary/term_extractor.py` | SudachiPy + LLM判定に刷新 |
| `tests/test_term_extractor.py` | 新アーキテクチャ用に書き換え |

### 関連用語機能の削除
| ファイル | 削除内容 |
|---------|---------|
| `src/genglossary/models/term.py` | `related_terms`, `add_related_term()` |
| `src/genglossary/glossary_generator.py` | `_extract_related_terms()`, `RelatedTermsResponse` |
| `src/genglossary/glossary_refiner.py` | `RefinementResponse.related_terms`, マージ処理 |
| `src/genglossary/output/markdown_writer.py` | `_format_related_terms()` |
| `tests/` 各ファイル | 関連用語のテスト |

## Notes

- 計画ファイル: `/Users/endo5501/.claude/plans/sunny-exploring-crane.md`
- TDD（テスト駆動開発）で進める
- SudachiPyの分割モードはC（長単位）を使用
- 固有名詞のみを抽出対象とする
