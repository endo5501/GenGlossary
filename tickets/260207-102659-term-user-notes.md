---
priority: 2
tags: [feature, frontend, backend, pipeline, llm]
description: "Add user notes to terms for supplementary context used in glossary generation"
created_at: "2026-02-07T10:26:59Z"
started_at: 2026-02-07T13:59:56Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# 用語への後付け補足情報（User Notes）機能

## 概要

現在、用語集の生成に使用される情報は入力ファイルの内容のみに限られている。ユーザーが各用語に対して補足情報（後付け情報）を追加し、その情報がパイプラインの各ステップ（Generate / Review / Refine）でLLMプロンプトに反映される仕組みを追加する。

これにより、ファイル内の文脈だけでは不十分な場合でも、ユーザーの知識を反映したより精度の高い用語集を作成できるようになる。

## ユースケース

- ファイル内では略称しか登場しない用語に、正式名称や背景を補足する
- 文脈からは読み取れない用語間の関係性を明示する
- LLMが誤った解釈をした用語に対して、正しい意味のヒントを与える
- 特定のドメイン知識（専門分野の慣例など）を補足する

**例:**
```
用語: "GP"
後付け情報: "この文書ではGPはGeneral Practitioner（一般開業医）の略称として使用されている"
→ LLMがこの補足を考慮して定義を生成
```

## UI配置: Terms画面

Terms画面の詳細パネルに補足情報の入力欄を追加する。

**理由:**
- 用語（`terms_extracted`）に直接紐づく情報であり、Terms画面が最も自然
- パイプラインの最上流にあるため、Generate→Review→Refineの全ステップで活用可能
- 再Extract時にも `user_notes` カラムは保持されるため永続性を確保しやすい

**UI案:**
```
┌──────────────────────────────────────┐
│ Terms画面 - 詳細パネル               │
├──────────────────────────────────────┤
│ 用語名: 量子もつれ                   │
│ カテゴリ: [technical_term ▼]         │
│                                      │
│ 補足情報:                            │
│ ┌──────────────────────────────────┐ │
│ │ 複数の量子ビットが相互に関連    │ │
│ │ し合う現象。EPRパラドックスと   │ │
│ │ も関連する概念。                │ │
│ └──────────────────────────────────┘ │
│              [保存]                  │
└──────────────────────────────────────┘
```

## 機能要件

### 1. データモデル

`terms_extracted` テーブルに `user_notes` カラムを追加:

```sql
ALTER TABLE terms_extracted ADD COLUMN user_notes TEXT DEFAULT '';
```

- 再Extract時の挙動: 既存の `user_notes` は保持される（Extract処理は `user_notes` カラムを上書きしない）
- スキーマバージョンの更新が必要

### 2. バックエンドAPI

既存の用語更新APIに `user_notes` フィールドを追加:

- `PATCH /api/projects/{project_id}/terms/{term_id}` — `user_notes` の更新に対応
- `GET` レスポンスに `user_notes` を含める

### 3. フロントエンドUI

Terms画面の詳細パネルに:
- `Textarea` による補足情報の入力欄を追加（カテゴリ選択の下に配置）
- **採用: 自動保存（debounce 500ms）** で `PATCH` APIを自動呼び出し
- 保存中はインジケーター表示（"保存中..." → "保存済み"）

### 4. パイプラインへの統合

各ステップのLLMプロンプトに `user_notes` を注入する:

#### Generate ステップ（`GlossaryGenerator`）
- `_build_definition_prompt()` に `user_notes` パラメータを追加
- 補足情報がある用語は「ユーザー補足情報」セクションとしてプロンプトに含める

#### Review ステップ（`GlossaryReviewer`）
- `_create_review_prompt()` で各用語の情報に `user_notes` を付記
- レビュアーが補足情報も考慮して矛盾・問題を検出

#### Refine ステップ（`GlossaryRefiner`）
- `_create_refinement_prompt()` で `user_notes` を含める
- 改善時に補足情報を根拠として活用

### 5. 再Extract時のデータ保持

Extract処理で `terms_extracted` テーブルをクリア・再作成する際、既存の `user_notes` を保持する仕組みが必要:

- **採用: 方針A**: Extract前に `user_notes` をバックアップし、Extract後に `term_text` をキーにして復元
  - `backup_user_notes(conn)` → `{term_text: user_notes}` の辞書を返す
  - `restore_user_notes(conn, notes_map)` → `term_text` をキーに `user_notes` を復元
- ~~方針B: Extract処理で既存行を削除せず、UPSERT に変更~~ → 既存フローへの影響が大きいため不採用

## データフロー

```
ユーザー → Terms画面で user_notes 入力
                ↓
        terms_extracted.user_notes に保存
                ↓
    ┌───────────────────────────────────────────┐
    │ Generate:                                 │
    │   list_all_terms() で user_notes 取得     │
    │   → プロンプトに「ユーザー補足情報」注入  │
    │   → LLMが考慮して定義生成                 │
    ├───────────────────────────────────────────┤
    │ Review:                                   │
    │   provisional glossary + user_notes       │
    │   → プロンプトに補足情報を付記            │
    │   → 矛盾検出に補足情報も考慮             │
    ├───────────────────────────────────────────┤
    │ Refine:                                   │
    │   issues + glossary + user_notes          │
    │   → 改善時に補足情報を根拠として活用      │
    └───────────────────────────────────────────┘
                ↓
        より精度の高い最終用語集
```

## Tasks

- [x] DB: `terms_extracted` に `user_notes` カラム追加（スキーママイグレーション）
- [x] Model: Term モデルに `user_notes` フィールド追加
- [x] Repository: `term_repository` の CRUD 関数を `user_notes` 対応に更新
- [x] Repository: Extract時の `user_notes` 保持ロジック実装
- [x] API: 用語更新エンドポイントで `user_notes` の読み書きに対応
- [x] Frontend: Terms画面の詳細パネルに補足情報入力UI追加
- [x] Pipeline/Generator: `GlossaryGenerator._build_definition_prompt()` に `user_notes` 注入
- [x] Pipeline/Reviewer: `GlossaryReviewer._create_review_prompt()` に `user_notes` 注入
- [x] Pipeline/Refiner: `GlossaryRefiner._create_refinement_prompt()` に `user_notes` 注入
- [x] Pipeline/Executor: 各ステップ間での `user_notes` 受け渡し対応
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

- プロンプトインジェクション対策: `user_notes` はユーザー入力なので、LLMプロンプトに注入する際は既存の `wrap_user_data()` ユーティリティで安全にラップする
- `user_notes` が空の用語ではプロンプトに補足セクションを含めない（トークン節約）
- 将来的に Provisional / Refined 画面でも `user_notes` を読み取り表示できると、ユーザーが補足情報の反映状況を確認しやすくなる
- 「追加必須用語一覧」チケット（`260207-093417-required-terms-list`）で追加された必須用語にも `user_notes` を設定できると相乗効果がある
