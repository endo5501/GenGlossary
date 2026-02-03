---
priority: 2
tags: [bug, excluded-terms]
description: "除外用語が用語一覧に表示される問題"
created_at: "2026-02-03T19:24:59Z"
started_at: 2026-02-03T19:38:53Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# 除外用語が用語一覧に表示される問題

## 概要

除外用語に登録された用語が、Terms画面の用語一覧に依然として表示されています。除外用語は用語一覧から除外されるべきです。

## 期待される動作

1. 除外用語リストに登録された用語は、Terms画面の「用語一覧」タブに表示されない
2. 除外用語は「除外用語」タブでのみ表示される

## 現在の動作

除外用語に登録された用語が「用語一覧」タブにも表示されてしまう。

## 関連コード

- `src/genglossary/api/routers/terms.py`: 用語一覧取得API
- `src/genglossary/db/term_repository.py`: 用語取得ロジック
- フィルタリングロジックの追加が必要

## Tasks

- [ ] 用語一覧取得時に除外用語をフィルタリングする
- [ ] APIまたはリポジトリ層でフィルタリングを実装
- [ ] テストの追加
- [ ] Commit
- [ ] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [ ] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Update docs/architecture/*.md
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing


## 設計

**変更対象:** `src/genglossary/db/term_repository.py` の `list_all_terms()` 関数

**変更内容:**
```sql
-- 現在
SELECT * FROM terms_extracted ORDER BY id

-- 修正後
SELECT * FROM terms_extracted
WHERE term_text NOT IN (SELECT term_text FROM terms_excluded)
ORDER BY id
```

**テスト方針:**
1. 除外用語がない場合 → 全用語が返される
2. 除外用語がある場合 → 該当用語が除外される
3. 部分一致は除外しない（完全一致のみ）

## Notes

- リポジトリ層でSQLの`NOT IN`サブクエリを使用してフィルタリング
- API層の変更は不要
