---
priority: 1
tags: [feature, frontend, backend, terms]
description: "Add required terms list feature to Terms page - ensures specified terms always appear in glossary"
created_at: "2026-02-07T09:34:17Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# 追加必須用語一覧（Required Terms List）

## 概要

Terms画面に「追加必須用語一覧」機能を追加する。

現在、SudachiPyの形態素解析では正しく解析されない単語があったり、LLMにより`common_noun`と自動分類されて除外されてしまうケースがある。これにより、ユーザーが期待する用語が用語一覧に現れないことがある。

「追加必須用語一覧」は除外用語一覧の逆の機能であり、ここに登録された用語は、SudachiPyの解析結果やLLMの分類結果に関わらず、必ず用語一覧に含まれるようにする。

## 既存の除外用語機能との対比

| 項目 | 除外用語一覧 | 追加必須用語一覧（今回追加） |
|------|-------------|--------------------------|
| 目的 | 特定の用語を用語一覧から除外 | 特定の用語を用語一覧に必ず含める |
| DB テーブル | `terms_excluded` | `terms_required`（新規） |
| source | `auto` / `manual` | `manual` のみ |
| UI タブ | 「除外用語」タブ | 「必須用語」タブ（新規追加） |
| 用語抽出での効果 | 候補リストから除去 | 候補リストに強制追加 |

## 機能要件

### 1. データモデル

- `terms_required` テーブルを新規作成
  - `id`: INTEGER PRIMARY KEY AUTOINCREMENT
  - `term_text`: TEXT NOT NULL UNIQUE
  - `source`: TEXT NOT NULL（当面は `manual` のみ）
  - `created_at`: TEXT NOT NULL DEFAULT (datetime('now'))

### 2. バックエンドAPI

除外用語APIに倣い、以下のエンドポイントを追加:

- `GET /api/projects/{project_id}/required-terms` — 必須用語一覧の取得
- `POST /api/projects/{project_id}/required-terms` — 必須用語の追加
- `DELETE /api/projects/{project_id}/required-terms/{term_id}` — 必須用語の削除

### 3. フロントエンドUI

Terms画面のタブに「必須用語」タブを追加（除外用語タブと同様の構成）:

- 必須用語の一覧表示（用語テキスト、追加日時）
- 必須用語の手動追加（テキスト入力 + Addボタン）
- 必須用語の削除（各行に削除ボタン）

### 4. 用語抽出ロジックへの統合

`TermExtractor.extract_terms()` の処理フローに組み込み:

- SudachiPy解析後、除外用語フィルタリング後に、必須用語を候補リストにマージ
- LLMによる分類後、`common_noun` に分類されても必須用語は除外しない
- 最終的な用語リストに必須用語が必ず含まれることを保証


## Tasks

- [ ] DB: `terms_required` テーブルのスキーマ追加
- [ ] Model: `RequiredTerm` Pydanticモデルの作成
- [ ] Repository: `required_term_repository.py` のCRUD関数実装
- [ ] API: 必須用語エンドポイント（GET/POST/DELETE）の実装
- [ ] Frontend: `useRequiredTerms` フックの作成
- [ ] Frontend: Terms画面に「必須用語」タブの追加（一覧表示・追加・削除）
- [ ] TermExtractor: 必須用語のマージロジック追加（候補リストへの強制追加）
- [ ] TermExtractor: LLM分類結果から必須用語を除外しないガードの追加
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

- 除外用語と必須用語が競合する場合（同じ用語が両方に登録されている場合）の挙動は要検討。基本方針: 必須用語が優先される（除外より追加が優先）
- 除外用語一覧の実装（`excluded_term_repository.py`、`excluded_terms.py` router、`useExcludedTerms.ts`）を参考にする
- 将来的には、LLMの分類結果からユーザーが手動で必須用語に追加する操作（用語一覧の各行に「必須に追加」ボタン）も検討可能
