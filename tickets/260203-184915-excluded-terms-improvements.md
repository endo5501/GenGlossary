---
priority: 1
tags: [backend, bug-fix, performance]
description: "除外用語機能の品質改善（codexレビュー指摘事項）"
created_at: "2026-02-03T18:49:15Z"
started_at: 2026-02-03T19:00:16Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# 除外用語機能の品質改善

## 概要

除外用語機能（260203-092010-terms-exclusion-list）のcodex MCPレビューで指摘された改善点を実装する。

## 指摘事項

### Major（重要）

#### 1. create_excluded_termのレースコンディション

**ファイル**: `src/genglossary/api/routers/excluded_terms.py`
**関数**: `create_excluded_term`（約30-60行目）

**現状の問題**:
```python
# 現在のコード（問題あり）
exists = term_exists_in_excluded(project_db, request.term_text)
if exists:
    # ...
term_id = add_excluded_term(project_db, request.term_text, "manual")
# ↑ この間に別リクエストがinsertすると不整合
```

**対策**:
1. `src/genglossary/db/excluded_term_repository.py`に`get_excluded_term_by_id`関数を追加
2. `add_excluded_term`の戻り値を`tuple[int, bool]`に変更（ID, 新規作成かどうか）
3. ルーターでexistsチェックを削除し、戻り値で判断

#### 2. bulk_add_excluded_termsの正規化不足

**ファイル**:
- `src/genglossary/db/excluded_term_repository.py` - `bulk_add_excluded_terms`関数
- `src/genglossary/term_extractor.py` - `_add_common_nouns_to_exclusion`メソッド

**現状の問題**:
```python
# LLM出力に空白が含まれている場合
common_nouns = ["  用語A  ", "用語B"]  # 前後に空白
bulk_add_excluded_terms(conn, common_nouns, "auto")
# → DB: "  用語A  " として保存

# フィルタリング時
candidates = ["用語A"]  # 空白なし
excluded = get_excluded_term_texts(conn)  # {"  用語A  "}
# → "用語A" not in {"  用語A  "} → フィルタされない！
```

**対策**:
```python
# bulk_add_excluded_terms内で正規化
def bulk_add_excluded_terms(..., term_texts: list[str], ...):
    normalized = [t.strip() for t in term_texts if t.strip()]
    # ...
```

#### 3. 非効率なfetchパターン

**ファイル**: `src/genglossary/api/routers/excluded_terms.py`
**関数**: `create_excluded_term`（約50行目付近）

**現状の問題**:
```python
# INSERT後に全件取得してO(n)検索
terms = get_all_excluded_terms(project_db)
term = next((t for t in terms if t.id == term_id), None)
```

**対策**:
```python
# src/genglossary/db/excluded_term_repository.py に追加
def get_excluded_term_by_id(conn: sqlite3.Connection, term_id: int) -> ExcludedTerm | None:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM terms_excluded WHERE id = ?", (term_id,))
    row = cursor.fetchone()
    if not row:
        return None
    return ExcludedTerm(...)

# ルーターで使用
term = get_excluded_term_by_id(project_db, term_id)
```

### Minor（軽微）

#### 4. validation重複

**ファイル**:
- `src/genglossary/models/excluded_term.py` - `field_validator("term_text")`
- `src/genglossary/api/schemas/excluded_term_schemas.py` - `Field(..., min_length=1)`

**対策**: モデル層のバリデーションを削除し、API層のみでバリデーション

#### 5. 大文字小文字を区別したマッチング

**ファイル**: `src/genglossary/term_extractor.py`
**メソッド**: `_filter_excluded_terms`

**現状**: `if c not in excluded` は完全一致（case-sensitive）

**検討事項**: 日本語用語が主なので影響は限定的だが、英語用語の場合は問題になる可能性

### Suggestion（提案）

#### 6. queryKeyのprojectId!使用

**ファイル**: `frontend/src/api/hooks/useExcludedTerms.ts`
**行**: 約27行目

```typescript
// 現状
queryKey: excludedTermKeys.list(projectId!),  // undefinedの可能性

// 改善案
queryKey: excludedTermKeys.list(projectId ?? 0),
```

#### 7. 削除時のterms invalidate

**ファイル**: `frontend/src/api/hooks/useExcludedTerms.ts`
**関数**: `useDeleteExcludedTerm`

```typescript
// 現状
onSuccess: () => {
  queryClient.invalidateQueries({ queryKey: excludedTermKeys.list(projectId) })
}

// 改善案（createと同様にtermsもinvalidate）
onSuccess: () => {
  queryClient.invalidateQueries({ queryKey: excludedTermKeys.list(projectId) })
  queryClient.invalidateQueries({ queryKey: termKeys.list(projectId) })
}
```

## Tasks

- [x] `src/genglossary/db/excluded_term_repository.py`: `get_excluded_term_by_id`関数を追加
- [x] `src/genglossary/api/routers/excluded_terms.py`: レースコンディション対策（existsチェック削除）
- [x] `src/genglossary/db/excluded_term_repository.py`: `bulk_add_excluded_terms`に正規化処理追加
- [x] `frontend/src/api/hooks/useExcludedTerms.ts`: `useDeleteExcludedTerm`でtermKeysもinvalidate
- [x] Commit
- [x] Run tests (`uv run pytest` & `pnpm test`)

## Notes

- 機能は動作するが、並行処理やエッジケースでの堅牢性に問題がある
- パフォーマンス改善（O(n)→O(1)）も含む
