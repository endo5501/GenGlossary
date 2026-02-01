---
priority: 1
tags: [bug, frontend, critical]
description: "各画面の再生成ボタン（Review, Regenerate等）が反応しない"
created_at: "2026-02-01T15:32:10Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# 各画面の再生成ボタンが機能しない

## 概要

Issues画面の[Review]ボタン、Provisional画面の[Regenerate]ボタンなど、各画面の再生成ボタンを押しても何も反応がない。

## 期待する動作

- **Issues画面 [Review]ボタン**: Provisionalの結果からReviewステップのみ再実行
- **Provisional画面 [Regenerate]ボタン**: 抽出済み用語から用語集生成ステップのみ再実行
- 各ボタンは対応する `PipelineScope` を使って部分的なパイプライン実行を行う

## 現状の問題

- ボタンを押しても反応がない
- Issuesの結果を得るには最初から全パイプラインを実行する必要がある
- 部分的な再処理ができないため、デバッグや微調整に時間がかかる

## 調査ポイント

- フロントエンドのボタンイベントハンドラ
- API呼び出し（`POST /api/projects/{id}/runs`）が正しく行われているか
- `scope` パラメータ（`from_terms`, `provisional_to_refined`）が正しく渡されているか
- バックエンドで対応するスコープが正しく処理されているか

## 関連するスコープ

| 画面 | ボタン | 期待するscope |
|------|--------|---------------|
| Terms | Regenerate | `from_terms` |
| Provisional | Regenerate | `from_terms` |
| Issues | Review | `provisional_to_refined` |
| Refined | Regenerate | `provisional_to_refined` |

## Tasks

- [ ] フロントエンドのボタンイベントハンドラを確認
- [ ] APIリクエストが送信されているか確認（DevTools）
- [ ] バックエンドのスコープ処理を確認
- [ ] 問題の特定と修正
- [ ] Commit
- [ ] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [ ] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Update docs/architecture/*.md
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing


## Notes

- 元の設計では部分的なパイプライン実行が可能なはずだった
- `PipelineScope` enum: `FULL`, `FROM_TERMS`, `PROVISIONAL_TO_REFINED`
