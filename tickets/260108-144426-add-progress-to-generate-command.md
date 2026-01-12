---
priority: 2
tags: [enhancement, cli, progress-display]
description: "Add detailed progress display to glossary generation command"
created_at: "2026-01-08T14:44:26Z"
started_at: 2026-01-09T21:11:09Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# Add Progress Display to Generate Command

## Overview

現在、`uv run genglossary generate` コマンドで用語集を生成する際、進捗が表示されません。`analyze-terms` コマンドのように、以下の進捗情報を表示する必要があります：

1. 用語集生成中の各ステップ（用語ごとの定義生成）の進捗
2. 精査（review）ステップの進捗
3. 改善（refine）ステップの進捗
4. 各ステップの経過時間
5. 推定残り時間（可能であれば）

## Tasks

- [x] Analyze current progress display in `analyze-terms` command
- [x] Design progress display format for `generate` command
- [x] Add progress display to `GlossaryGenerator` (Step 2: 用語集生成)
- [x] Add progress display to `GlossaryReviewer` (Step 3: 精査)
- [x] Add progress display to `GlossaryRefiner` (Step 4: 改善)
- [x] Update CLI to show overall pipeline progress
- [x] Add tests for progress display functionality
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing


## Notes

### 現状の問題点
- `analyze-terms` では進捗が詳細に表示されている
- `generate` では進捗がほとんど表示されない
- 長時間かかる処理で、ユーザーは進捗が分からず不安

### 実装の考慮事項
- `rich` ライブラリの `Progress` クラスを活用
- 各ステップでの LLM API 呼び出し回数を事前に計算
- タイムアウトやエラー時の表示も考慮
- `analyze-terms` の実装を参考にする

## Implementation Summary

### 実装内容

TDDサイクル（Red → Green → Commit）に従って実装完了：

#### 1. GlossaryGenerator (src/genglossary/glossary_generator.py)
- `progress_callback: ProgressCallback | None = None` パラメータを `generate()` メソッドに追加
- 各用語の定義生成後に `progress_callback(current, total)` を呼び出し
- テスト3件追加（すべて通過）
- コミット: `1332ff7`, `89f3bb6`

#### 2. GlossaryRefiner (src/genglossary/glossary_refiner.py)
- `progress_callback: ProgressCallback | None = None` パラメータを `refine()` メソッドに追加
- 各問題の解決後に `progress_callback(current, total)` を呼び出し
- テスト3件追加（すべて通過）
- コミット: `33cbb06`, `175cf5f`

#### 3. CLI (src/genglossary/cli.py)
- Step 3（用語集生成）：`Progress` + `BarColumn` + `TaskProgressColumn` + `TimeElapsedColumn`
- Step 4（精査）：`Progress` + `SpinnerColumn` + `TimeElapsedColumn`（単一LLM呼び出しのため）
- Step 5（改善）：`Progress` + `BarColumn` + `TaskProgressColumn` + `TimeElapsedColumn`
- `--verbose` フラグ使用時のみ表示
- コミット: `03e9ac0`

### 進捗表示例

```
⣾ 定義を生成中... [████████░░░░░░░░] 5/15  0:00:45
⣾ 精査中...  0:00:08
⣾ 改善中... [████████████████████] 3/3  0:00:15
```

### テスト結果
- ✅ 全265ユニットテスト通過
- ✅ 静的解析（pyright）エラーなし
- ✅ 既存機能に影響なし

### 動作確認コマンド

```bash
uv run genglossary generate -i ./target_docs -o ./output/test.md --verbose
```
