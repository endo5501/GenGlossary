---
priority: 1
tags: [enhancement, term-extraction, llm]
description: "用語抽出処理の精度向上 - プロンプト改善とフィルタリング機構の追加"
created_at: "2026-01-01T10:57:54Z"
started_at: 2026-01-01T11:00:52Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# 用語抽出精度向上

## 概要

TermExtractorの用語抽出精度を向上させる。一般的な単語や動詞的フレーズを除外し、固有名詞・専門用語に絞った用語集を生成する。

### 現在の問題
- プロンプトの抽出基準が曖昧
- 一般的な単語（「借金」「ビール」）が抽出される
- 動詞的フレーズ（「法則の発見」「死戦を潜り抜ける」）が抽出される
- 描写表現（「顔が良い」「銀色の髪」）が抽出される

### 方針
**ハイブリッドアプローチ**: プロンプト改善（主軸）+ 軽量フィルタリング（補助）

- 固有名詞（人名・地名・作品固有の名称）は用語集に含める
- 外部依存なし（標準ライブラリのみで実装）

## Tasks

### Step 1: フィルタリングテスト作成
- [x] `tests/test_term_extractor.py` に `TestTermFiltering` クラスを追加
- [x] 動詞句フィルタのテストを作成
- [x] 形容詞句フィルタのテストを作成
- [x] 短いひらがなフィルタのテストを作成
- [x] `uv run pytest tests/test_term_extractor.py` → 失敗確認
- [x] コミット: "Add tests for term filtering functionality"

### Step 2: フィルタリング実装
- [x] `_should_filter_term` メソッドを追加
- [x] `_is_only_hiragana` ヘルパーメソッドを追加
- [x] `_process_terms` でフィルタを呼び出すよう修正
- [x] `uv run pytest tests/test_term_extractor.py` → パス確認
- [x] コミット: "Implement term filtering in TermExtractor"

### Step 3: プロンプト改善テスト作成
- [x] `TestPromptGeneration` クラスを追加
- [x] 新しいプロンプト要素のテストを作成
- [x] `uv run pytest tests/test_term_extractor.py` → 失敗確認
- [x] コミット: "Add tests for improved extraction prompt"

### Step 4: プロンプト改善実装
- [x] `_create_extraction_prompt` メソッドを更新
- [x] `uv run pytest tests/test_term_extractor.py` → パス確認
- [x] コミット: "Improve extraction prompt for better term precision"

### Step 5: 動作確認
- [x] `uv run genglossary generate --input tmp/example2 --output tmp/test_output.md`
- [x] 抽出結果を確認し、精度向上を検証

### 完了条件
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing

## 修正対象ファイル

| ファイル | 変更内容 |
|---------|---------|
| `src/genglossary/term_extractor.py` | プロンプト改善、フィルタリング追加 |
| `tests/test_term_extractor.py` | 新規テストクラス追加 |

## 技術詳細

### 新しいプロンプト（抜粋）

```
## 抽出すべき用語（含める）
- 固有名詞: 人名、地名、組織名、作品固有の名称
- 専門用語: その文脈で特別な意味を持つ語
- 造語・特殊用語: 作品やドキュメント固有の造語

## 抽出しない用語（除外）
- 一般名詞: 辞書で意味が自明な日常語
- 動詞・動詞句: 「〜する」「〜を発見」など
- 形容詞句・描写表現: 「顔が良い」「銀色の髪」など
```

### フィルタリングルール

1. 1文字以下の用語を除外
2. 動詞句パターン（`する`, `された`, `を発見` 等）を除外
3. 形容詞句パターン（`が良い`, `の髪` 等）を除外
4. 4文字以下のひらがなのみの用語を除外

## Notes

- 計画ファイル: `/Users/endo5501/.claude/plans/sunny-exploring-crane.md`
- TDD（テスト駆動開発）で進める
- 既存の12テストとの互換性を維持
