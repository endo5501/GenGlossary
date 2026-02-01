---
priority: 3
tags: [ux, frontend]
description: "左サイドバーの各メニューに処理中インジケーターを追加し、現在のシーケンスを可視化"
created_at: "2026-02-01T12:48:09Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# サイドバー処理中インジケーター

## 概要

左サイドバーの各選択メニューのボタンに、処理中であることを示すマーク（アイコンや点滅など）を追加し、
現在どのシーケンス（ステップ）を実行しているかをわかりやすくする。

## 現状の問題

- パイプライン実行中、どのステップを処理しているかが視覚的にわからない
- ユーザーは処理の進捗を把握しづらい

## 期待する動作

- 処理中のステップに対応するサイドバーメニューに、視覚的なインジケーターを表示
  - 例: スピナーアイコン、点滅エフェクト、バッジなど
- 処理が完了したらインジケーターを消す、または完了マークに変更

## 対象メニュー項目

1. Files
2. Terms
3. Provisional
4. Issues
5. Refined
6. Document Viewer

## Tasks

- [ ] 現在の処理ステップを追跡する状態管理の実装
- [ ] サイドバーメニューへのインジケーターUI追加
- [ ] 処理開始/完了時のインジケーター更新ロジック
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

- パイプラインの各ステップとサイドバーメニューの対応関係を明確にする
- アクセシビリティ（視覚障害者向け）も考慮する
