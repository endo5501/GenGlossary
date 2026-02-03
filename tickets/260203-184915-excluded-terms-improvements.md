---
priority: 4
tags: [backend, bug-fix, performance]
description: "除外用語機能の品質改善（codexレビュー指摘事項）"
created_at: "2026-02-03T18:49:15Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# 除外用語機能の品質改善

## 概要

除外用語機能（260203-092010-terms-exclusion-list）のcodex MCPレビューで指摘された改善点を実装する。

## 指摘事項

### Major（重要）

#### 1. create_excluded_termのレースコンディション
**ファイル**: `src/genglossary/api/routers/excluded_terms.py`

現状: existsチェック後にinsertしているため、並行リクエストで不整合が発生する可能性
- チェックとインサートの間に別リクエストがインサートすると、201を返すが実際は既存
- インサート後のfetch前に削除されると`assert term is not None`でクラッシュ

**対策**: `add_excluded_term`が挿入されたかどうかを返すようにし、IDで直接取得

#### 2. bulk_add_excluded_termsの正規化不足
**ファイル**: `src/genglossary/term_extractor.py`, `src/genglossary/db/excluded_term_repository.py`

現状: LLM出力をそのまま保存しており、空白やケースバリアントがあると`_filter_excluded_terms`の完全一致で除外に失敗

**対策**: リポジトリ層またはインサート前にtrimと正規化を実施

#### 3. 非効率なfetchパターン
**ファイル**: `src/genglossary/api/routers/excluded_terms.py`

現状: INSERT後に全件取得してO(n)検索
**対策**: `get_excluded_term_by_id`クエリを追加

### Minor（軽微）

#### 4. validation重複
model（`excluded_term.py`）とschema（`excluded_term_schemas.py`）で同じバリデーション

#### 5. 大文字小文字を区別したマッチング
除外リストのマッチングがcase-sensitive

### Suggestion（提案）

#### 6. queryKeyのprojectId!使用
**ファイル**: `frontend/src/api/hooks/useExcludedTerms.ts`

`enabled`ガードがあるため安全だが、フォールバック値を使用した方が堅牢

#### 7. 削除時のterms invalidate
除外用語削除時に`termKeys.list`をinvalidateしていない

## Tasks

- [ ] `get_excluded_term_by_id`リポジトリ関数を追加
- [ ] create_excluded_termのレースコンディション対策
- [ ] bulk_add_excluded_termsの正規化処理追加
- [ ] useDeleteExcludedTermでtermKeysもinvalidate
- [ ] Commit
- [ ] Run tests

## Notes

- 機能は動作するが、並行処理やエッジケースでの堅牢性に問題がある
- パフォーマンス改善（O(n)→O(1)）も含む
