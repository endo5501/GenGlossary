---
priority: 3
tags: [feature, frontend, backend, pipeline, llm]
description: "Add synonym linking between terms to aggregate context and improve glossary accuracy"
created_at: "2026-02-07T10:42:02Z"
started_at: 2026-02-07T15:14:19Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# 用語の同義語リンク（Synonym Linking）機能

## 概要

現在、用語はすべて文字列の完全一致で管理されているため、同じ概念を指す異なる表記が別々の用語として扱われ、それぞれ独立して解析される。結果として、1つの概念に関する情報が分散し、用語集の精度が低下する。

用語間に「同義（synonym）」の関連を設定し、解析時には同義語グループの出現情報を統合してLLMに渡すことで、より正確な定義を生成できるようにする。

## 問題の具体例

### 人名の呼び方の違い
```
用語一覧に以下が別々に存在:
  ・「田中太郎」   → 出現3箇所
  ・「田中」       → 出現12箇所
  ・「田中部長」   → 出現5箇所

現状: それぞれ独立して解析 → 各3件/12件/5件のコンテキストのみ
改善後: 同義語として統合 → 20件のコンテキストをまとめて解析
```

### 表記揺れ
```
  ・「サーバー」と「サーバ」
  ・「インターフェース」と「インタフェース」
  ・「データベース」と「DB」
```

### 略称・正式名称
```
  ・「AI」と「人工知能」と「Artificial Intelligence」
```

## データモデル

### 同義語グループテーブル（新規）

```sql
CREATE TABLE IF NOT EXISTS term_synonym_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    primary_term_text TEXT NOT NULL,  -- グループの代表用語
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

### 同義語メンバーテーブル（新規）

```sql
CREATE TABLE IF NOT EXISTS term_synonym_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL REFERENCES term_synonym_groups(id) ON DELETE CASCADE,
    term_text TEXT NOT NULL UNIQUE,  -- 各メンバー用語（重複所属不可）
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

**設計ポイント:**
- 1つの用語は最大1つの同義語グループにのみ所属（UNIQUE制約）
- グループには「代表用語（primary_term_text）」を設定 → 用語集にはこの名前で掲載
- `terms_extracted` とは `term_text` で紐づく（既存のテキストベース参照を踏襲）

### データ例

```
term_synonym_groups:
  id=1, primary_term_text="田中太郎"

term_synonym_members:
  group_id=1, term_text="田中太郎"
  group_id=1, term_text="田中"
  group_id=1, term_text="田中部長"
```

## UI

### Terms画面への追加

Terms画面の詳細パネルに同義語管理UIを追加する。

**UI案:**
```
┌──────────────────────────────────────┐
│ Terms画面 - 詳細パネル               │
├──────────────────────────────────────┤
│ 用語名: 田中太郎                     │
│ カテゴリ: [person_name ▼]           │
│                                      │
│ 同義語グループ:                      │
│ ┌──────────────────────────────────┐ │
│ │ ★ 田中太郎（代表）    [解除]    │ │
│ │   田中                [解除]    │ │
│ │   田中部長            [解除]    │ │
│ └──────────────────────────────────┘ │
│ [+ 同義語を追加]                     │
│                                      │
│ ※ 代表用語の名前で用語集に掲載      │
└──────────────────────────────────────┘
```

**操作:**
- **同義語を追加**: 既存の用語一覧から選択して同義語グループに追加
- **解除**: グループからメンバーを削除（代表用語の場合は別のメンバーが代表に昇格、またはグループ解散）
- **代表用語の変更**: グループ内のメンバーをクリックして代表に設定

## バックエンドAPI

```
GET    /api/projects/{project_id}/synonym-groups          — 全グループ一覧
POST   /api/projects/{project_id}/synonym-groups          — グループ作成
DELETE /api/projects/{project_id}/synonym-groups/{id}      — グループ削除
POST   /api/projects/{project_id}/synonym-groups/{id}/members  — メンバー追加
DELETE /api/projects/{project_id}/synonym-groups/{id}/members/{member_id} — メンバー削除
PATCH  /api/projects/{project_id}/synonym-groups/{id}      — 代表用語変更
```

## パイプラインへの統合

### GlossaryGenerator（最も重要な変更）

`_find_term_occurrences()` で、対象用語の同義語もまとめて検索し、出現箇所を統合する。

**現在:**
```python
def _find_term_occurrences(self, term, documents):
    pattern = self._build_search_pattern(term)  # "田中太郎" のみ検索
    # → 3件のコンテキスト
```

**変更後:**
```python
def _find_term_occurrences(self, term, documents, synonyms=None):
    search_terms = [term] + (synonyms or [])  # ["田中太郎", "田中", "田中部長"]
    # 各同義語で検索し、出現箇所を統合
    # → 20件のコンテキスト（MAX_CONTEXT_COUNT で制限）
```

`_build_definition_prompt()` にも同義語情報を含める:

```
## 今回の用語:
用語: 田中太郎
同義語: 田中, 田中部長
出現箇所とコンテキスト:
（統合された20件から最大5件を選択）
```

### GlossaryReviewer

レビュー時に同義語グループの情報を提供し、同義語間の定義の一貫性もチェック対象にする。

### GlossaryRefiner

改善時に同義語の出現コンテキストも参照可能にする。

### 用語集出力（MarkdownWriter）

代表用語の項目に同義語を記載:

```markdown
## 田中太郎
**別名**: 田中、田中部長
**定義**: ...
```

## 再Extract時の挙動

- 同義語グループは `terms_extracted` とは独立したテーブルのため、再Extract後もグループ情報は保持される
- ただし、再Extract後にメンバーの `term_text` が `terms_extracted` に存在しなくなった場合の扱いが必要:
  - 方針: 孤立メンバーはグループに残すが、UI上で「未抽出」として表示。パイプライン実行時は出現箇所検索にのみ利用

## Tasks

- [ ] DB: `term_synonym_groups` / `term_synonym_members` テーブルのスキーマ追加
- [ ] Model: `SynonymGroup` / `SynonymMember` Pydanticモデルの作成
- [ ] Repository: `synonym_repository.py` のCRUD関数実装（グループ作成・削除、メンバー追加・削除・代表変更）
- [ ] Repository: 用語テキストから所属グループと同義語一覧を取得するクエリ
- [ ] API: 同義語グループエンドポイント（GET/POST/DELETE/PATCH）の実装
- [ ] Frontend: `useSynonymGroups` フックの作成
- [ ] Frontend: Terms画面の詳細パネルに同義語管理UI追加
- [ ] Pipeline/Generator: `_find_term_occurrences()` を同義語対応に拡張（出現箇所統合）
- [ ] Pipeline/Generator: `_build_definition_prompt()` に同義語情報を含める
- [ ] Pipeline/Reviewer: レビュープロンプトに同義語情報を付加
- [ ] Pipeline/Refiner: 改善プロンプトに同義語の出現コンテキストも参照可能にする
- [ ] Pipeline/Executor: パイプライン実行時に同義語グループをDBから読み込み各ステップに渡す
- [ ] Output: MarkdownWriterで代表用語に別名を記載
- [ ] Commit
- [ ] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [ ] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Update docs/architecture/*.md
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing


## Design

### 実装方針
- ボトムアップで実装: DB → Model → Repository → API → Frontend → Pipeline
- TDDで各レイヤーのテストを先に書く

### 1. データベースとモデル

**DBスキーマ（v7 → v8）**

`schema.py` の `initialize_db()` に2テーブルを追加。マイグレーション関数 `_migrate_v7_to_v8()` で既存DBに対応。

```sql
CREATE TABLE IF NOT EXISTS term_synonym_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    primary_term_text TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS term_synonym_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL REFERENCES term_synonym_groups(id) ON DELETE CASCADE,
    term_text TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

**Pydanticモデル（`models/synonym.py`）**

- `SynonymMember(id, group_id, term_text)`
- `SynonymGroup(id, primary_term_text, members: list[SynonymMember])`

**リポジトリ（`db/synonym_repository.py`）**

- `create_group(conn, primary_term_text, member_texts) -> int`
- `delete_group(conn, group_id)`
- `add_member(conn, group_id, term_text)`
- `remove_member(conn, member_id)`
- `update_primary_term(conn, group_id, new_primary_text)`
- `list_groups(conn) -> list[SynonymGroup]`
- `get_synonyms_for_term(conn, term_text) -> list[str]`

### 2. API エンドポイント

**ルーター（`api/routers/synonym_groups.py`）**

```
GET    /api/projects/{pid}/synonym-groups                — 全グループ一覧
POST   /api/projects/{pid}/synonym-groups                — グループ作成
DELETE /api/projects/{pid}/synonym-groups/{gid}           — グループ削除
PATCH  /api/projects/{pid}/synonym-groups/{gid}           — 代表用語変更
POST   /api/projects/{pid}/synonym-groups/{gid}/members   — メンバー追加
DELETE /api/projects/{pid}/synonym-groups/{gid}/members/{mid} — メンバー削除
```

**APIスキーマ（`api/schemas/synonym_group_schemas.py`）**

- `SynonymGroupResponse(id, primary_term_text, members[])`
- `SynonymGroupCreateRequest(primary_term_text, member_texts[])`
- `SynonymGroupUpdateRequest(primary_term_text)`
- `SynonymMemberCreateRequest(term_text)`

### 3. フロントエンド

- `api/types.ts` に `SynonymGroupResponse`, `SynonymMemberResponse` 型追加
- `api/hooks/useSynonymGroups.ts` フック作成（CRUD操作）
- `components/common/SynonymGroupPanel.tsx` コンポーネント作成
- `TermsPage.tsx` の詳細パネルに `SynonymGroupPanel` を統合

### 4. パイプライン統合

**GlossaryGenerator:**
- `_find_term_occurrences()` に `synonyms` 引数追加、同義語でも検索し出現箇所を統合
- `_build_definition_prompt()` に同義語情報を追記
- `generate()` に `synonym_groups` 引数追加、代表用語のみ用語集に掲載

**GlossaryReviewer:**
- `review()` に `synonym_groups` 引数追加、同義語間の一貫性チェック

**GlossaryRefiner:**
- `refine()` に `synonym_groups` 引数追加、同義語の出現コンテキスト参照

**PipelineExecutor:**
- 実行開始時にDBから同義語グループを一括読み込み、各ステップに渡す

**MarkdownWriter:**
- `write()` に `synonym_groups` 引数追加、代表用語に `**別名**` を追記

## Notes

- 同義語グループの用語は用語集では代表用語1件として掲載される（メンバー分だけ項目が増えることはない）
- 将来的にはLLMによる同義語候補の自動提案も検討可能（Extract時に類似度の高い用語ペアを提案）
- 「追加必須用語一覧」チケット（`260207-093417`）で追加された必須用語も同義語グループに参加可能
- 「後付け補足情報」チケット（`260207-102659`）の `user_notes` は代表用語に設定すればグループ全体に適用される
- `filter_contained_terms` は現在、部分文字列の包含関係で短い用語を除外するが、同義語機能ではユーザーが明示的にグループ化するため競合しない
