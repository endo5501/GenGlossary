---
priority: 2
tags: [enhancement, cli, progress-display]
description: "Add detailed progress display to glossary generation command"
created_at: "2026-01-08T14:44:26Z"
started_at: null  # Do not modify manually
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

- [ ] Analyze current progress display in `analyze-terms` command
- [ ] Design progress display format for `generate` command
- [ ] Add progress display to `GlossaryGenerator` (Step 2: 用語集生成)
- [ ] Add progress display to `GlossaryReviewer` (Step 3: 精査)
- [ ] Add progress display to `GlossaryRefiner` (Step 4: 改善)
- [ ] Update CLI to show overall pipeline progress
- [ ] Add tests for progress display functionality
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing


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
