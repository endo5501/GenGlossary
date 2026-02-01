---
priority: 1
tags: [bug, frontend, critical]
description: "各画面の再生成ボタン（Review, Regenerate等）が反応しない"
created_at: "2026-02-01T15:32:10Z"
started_at: 2026-02-01T15:44:06Z # Do not modify manually
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

## 設計（確定）

### 新しいスコープ設計

| スコープ | 実行ステップ | 用途 |
|----------|-------------|------|
| `full` | extract → generate → review → refine | 全体実行 (Run ボタン) |
| `extract` | extract のみ | Terms の Extract ボタン |
| `generate` | generate のみ | Provisional の Regenerate ボタン |
| `review` | review のみ | Issues の Review ボタン |
| `refine` | refine のみ | Refined の Regenerate ボタン |

### 削除するスコープ
- `from_terms`
- `provisional_to_refined`

### 変更箇所

**バックエンド:**
1. `PipelineScope` enum を更新
2. 各ステップ単独実行のハンドラを追加
3. 不要なスコープとハンドラを削除
4. `RunStartRequest` のバリデーションパターンを更新

**フロントエンド:**
1. `RunScope` 型を更新
2. 各フックを runs API 呼び出しに変更
3. 不要なエンドポイント呼び出しコードを削除

## Tasks

- [x] フロントエンドのボタンイベントハンドラを確認
- [x] バックエンドのスコープ処理を確認
- [x] 問題の特定と設計
- [x] バックエンド: PipelineScope enum を更新（TDD）
- [x] バックエンド: 各ステップ単独実行ハンドラを追加（TDD）
- [x] バックエンド: 不要なスコープを削除
- [x] フロントエンド: RunScope 型を更新
- [x] フロントエンド: 各フックを runs API 呼び出しに変更
- [x] フロントエンド: 不要なコードを削除
- [x] Commit
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Update docs/architecture/*.md
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing


## Notes

- 元の設計では部分的なパイプライン実行が可能なはずだった
- `PipelineScope` enum: `FULL`, `FROM_TERMS`, `PROVISIONAL_TO_REFINED`
