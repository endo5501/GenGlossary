---
priority: 2
tags: [ux, frontend, layout]
description: "Terms画面などで上部操作ボタンと下部ログを常時表示するレイアウトに修正"
created_at: "2026-02-01T12:48:08Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# 上部・下部メニューの常時表示レイアウト

## 概要

Terms画面などで、上部に操作ボタン、下部にログ表示があるが、
内部のリストが長くなると見えなくなってしまう問題を修正する。

## 現状の問題

- リスト内の項目が多くなると、画面全体がスクロールされる
- 上部の操作ボタンや下部のログ表示がスクロールで見えなくなる
- 操作するたびにスクロールし直す必要があり、使い勝手が悪い

## 期待する動作

- 上部メニュー（操作ボタン）は常に画面上部に固定表示
- 下部メニュー（ログ表示）は常に画面下部に固定表示
- 中央のリスト部分のみがスクロールする

## 影響範囲

- Terms画面
- その他同様のレイアウトを持つ画面

## Tasks

- [ ] レイアウト構造の見直し（sticky/fixed positioning）
- [ ] 中央コンテンツ部分のスクロール領域設定
- [ ] 各画面での動作確認
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

- CSSの `position: sticky` または `position: fixed` を活用
- レスポンシブ対応も考慮する
