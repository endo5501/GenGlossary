---
priority: 1
tags: [bugfix, frontend, backend]
description: "Required terms not reflected in term list, preventing synonym group assignment"
created_at: "2026-02-07T16:09:21Z"
started_at: 2026-02-08T04:58:09Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# 必須用語が用語一覧に反映されず同義語グループに追加できない

## 概要

必須用語一覧に追加した用語が、Terms画面の用語一覧に反映されていない。そのため、必須用語を同義語グループのメンバーとして追加することができない。

## 再現手順

1. 必須用語一覧に用語を追加する
2. Terms画面の用語一覧を確認する → 必須用語が表示されない
3. 同義語グループを作成し、必須用語をメンバーに追加しようとする → 候補に表示されない

## 期待される動作

- 必須用語一覧に追加した用語がTerms画面の用語一覧にも反映される
- 必須用語を同義語グループのメンバーとして追加できる

## Tasks

- [x] 原因調査：必須用語がTerms画面に表示されない理由を特定
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


## 原因分析

- `list_all_terms()` は `terms_extracted` テーブルのみをクエリしている
- `terms_required` テーブルの用語は含まれない
- フロントエンドの `SynonymGroupPanel` は `useTerms()` （= `terms_extracted` のみ）から候補を取得
- 同義語グループは `term_text` で管理されており、`terms_extracted` への FK制約はない → テキストさえ候補に出れば設定可能

## 設計

### アプローチ: バックエンドの `list_all_terms()` クエリを UNION 拡張

`term_repository.py` の `list_all_terms()` を修正し、`terms_extracted` と `terms_required` の UNION を返す。

```sql
SELECT id, term_text, category, user_notes FROM terms_extracted
WHERE NOT EXISTS (SELECT 1 FROM terms_excluded WHERE ...)
UNION ALL
SELECT -id, term_text, NULL, '' FROM terms_required
WHERE term_text NOT IN (SELECT term_text FROM terms_extracted)
  AND term_text NOT IN (SELECT term_text FROM terms_excluded)
ORDER BY term_text
```

- 必須用語のみの項目は `id < 0` で区別（PATCH/DELETE対象外）
- `terms_extracted` に既存の必須用語は重複しない
- フロントエンド変更不要（同義語候補に自動的に含まれる）

### 修正対象ファイル

- `src/genglossary/db/term_repository.py` - `list_all_terms()` のSQL修正

## Notes

- 必須用語一覧（required_terms）と抽出用語一覧（terms_extracted）のデータソースが異なるため、用語一覧のクエリが必須用語を含んでいない可能性が高い
