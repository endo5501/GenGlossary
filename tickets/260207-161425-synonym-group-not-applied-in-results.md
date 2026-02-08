---
priority: 1
tags: [bugfix, frontend, backend, pipeline]
description: "Synonym group members disappear from provisional/refined results and primary term lacks synonym info"
created_at: "2026-02-07T16:14:25Z"
started_at: 2026-02-08T01:21:37Z # Do not modify manually
closed_at: 2026-02-08T04:56:10Z # Do not modify manually
---

# 同義語グループの情報がProvisional以降の結果画面に反映されない

## 概要

同義語グループを設定して解析（Generate→Review→Refine）を実行した後、Provisional以降の結果画面で以下の問題が発生する：

1. 同義語グループに追加した非代表用語が一覧から消える
2. 代表用語は表示されるが、同義語グループの情報（別名等）が含まれていない

## 再現手順

1. Terms画面で同義語グループを作成（例：代表「田中太郎」、メンバー「田中」「田中部長」）
2. Full Pipelineを実行（Generate→Review→Refine）
3. Provisional画面を確認 → 「田中」「田中部長」が一覧にない
4. 「田中太郎」の項目を確認 → 同義語/別名の情報が表示されていない

## 期待される動作

- 代表用語「田中太郎」の項目に「別名：田中、田中部長」が表示される
- 非代表用語は代表用語に統合されたことがわかる表示になる

## 調査ポイント

- バックエンド側：パイプライン実行時に`synonym_groups`が正しく各ステップに渡されているか
- バックエンド側：MarkdownWriterで`**別名**`セクションが正しく生成されているか
- フロントエンド側：Provisional/Refined画面でMarkdownの別名セクションが正しくレンダリングされているか
- フロントエンド側：結果一覧のAPI応答に同義語情報が含まれているか

## Tasks

- [x] 原因調査：パイプライン実行時のsynonym_groups受け渡しを確認
- [x] 原因調査：結果画面のAPI応答内容を確認
- [x] 修正実装
- [x] Commit
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Update docs/architecture/*.md
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing


## 調査結果

### 根本原因
パイプライン実行時の synonym_groups 受け渡しは正常。問題はAPI層にある：
1. `GlossaryTermResponse` スキーマに aliases フィールドがない
2. provisional/refined APIエンドポイントが synonym_groups を読み込んでいない
3. `export-md` エンドポイントが手動Markdown生成しており別名セクションなし
4. フロントエンドが ProvisionalPage/RefinedPage で同義語情報をフェッチ/表示していない

### 修正方針（アプローチA: API拡張）

#### バックエンド
1. `GlossaryTermResponse` に `aliases: list[str]` フィールドを追加
2. `from_db_row` に aliases 引数を追加し synonym_groups からマッピング
3. provisional/refined APIエンドポイントで `list_groups()` を呼び aliases を付与
4. `export-md` に `**別名**` セクションを追加

#### フロントエンド
1. `GlossaryTermResponse` 型に `aliases: string[]` を追加
2. ProvisionalPage の detail パネルに aliases テキスト表示
3. RefinedPage の detail パネルに aliases テキスト表示

## Notes

- synonym-integrity-fixesチケット（260207-154049）の問題と関連する可能性あり
- パイプライン統合のテスト（test_synonym_pipeline.py）は通過しているため、フロントエンド表示側の問題の可能性が高い
