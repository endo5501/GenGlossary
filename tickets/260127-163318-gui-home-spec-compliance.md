---
priority: 2
tags: [gui, frontend, home]
description: "プロジェクト一覧画面（ホーム）の仕様準拠"
created_at: "2026-01-27T16:33:18Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# プロジェクト一覧画面（ホーム）の仕様準拠

## 概要

ホーム画面（プロジェクト一覧）をplan-gui.mdの仕様に完全準拠させる。

## 仕様 (plan-gui.md)

```
┌─────────────────────────────────────────────────────────────┐
│                         ホーム画面                           │
├────────────────────────────┬────────────────────────────────┤
│    【左ペイン】              │    【右ペイン】                 │
│    プロジェクト一覧          │    選択プロジェクトの概要カード   │
│                            │                                │
│  ┌─────┬────┬───┬───┬───┐  │  ・入力パス（target_docs相当） │
│  │名前 │更新│Doc│用語│iss│  │  ・LLM設定（provider/model）  │
│  ├─────┼────┼───┼───┼───┤  │  ・最終生成日時               │
│  │Proj1│... │ 5 │ 20│ 3 │  │                                │
│  │Proj2│... │ 3 │ 15│ 0 │  │  [開く] [複製] [削除]          │
│  └─────┴────┴───┴───┴───┘  │                                │
│                            │                                │
│       [新規作成]            │                                │
│       (一覧の下部)          │                                │
└────────────────────────────┴────────────────────────────────┘
```

## 現状の実装 (HomePage.tsx)

- 左ペイン: Name / Status / Last Run のみ ← **ドキュメント数・用語数・issues数が不足**
- 右ペイン: 概要カード + [Open]/[Clone]/[Delete]ボタン ← **ほぼ仕様通り**
- [新規作成]ボタン: ヘッダーにある ← **一覧の下部にあるべき**

## 修正対象ファイル

- `frontend/src/pages/HomePage.tsx`
- `src/genglossary/api/routers/projects.py` (統計情報を含めるよう拡張)
- `src/genglossary/api/schemas/project_schemas.py`

## Tasks

- [ ] 左ペイン（プロジェクト一覧）のカラムを変更: Name/Status/Last Run → 名前/最終更新/ドキュメント数/用語数/issues数
- [ ] [新規作成]ボタンを一覧の下部に移動
- [ ] バックエンドAPIで統計情報（ドキュメント数、用語数、issues数）を返すよう拡張
- [ ] 右ペイン（概要カード）の確認・調整
- [ ] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [ ] Code simplification review using code-simplifier agent
- [ ] Code review by codex MCP
- [ ] Update docs/architecture/*.md
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## Notes

- 右ペインの概要カードは既存実装でほぼ仕様通り
- バックエンドAPIの拡張が必要（プロジェクトごとの統計情報）
