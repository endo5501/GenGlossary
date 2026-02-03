---
priority: 2
tags: [refactoring, code-quality]
description: "除外用語機能のコード簡素化"
created_at: "2026-02-03T18:47:24Z"
started_at: 2026-02-03T19:07:03Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# 除外用語機能のコード簡素化

## 概要

除外用語機能（260203-092010-terms-exclusion-list）のcode-simplifierレビューで指摘された改善点を実装する。

## 改善提案

### 優先度高（即座に適用可能）

#### バックエンド

1. **`_process_terms`の簡素化**
   - ファイル: `src/genglossary/term_extractor.py`
   - 行: `_process_terms`メソッド（約200行目付近）
   - 変更内容: `seen` setの手動管理を`dict.fromkeys`に置き換え
   ```python
   # Before
   def _process_terms(self, terms: list[str]) -> list[str]:
       seen: set[str] = set()
       result: list[str] = []
       for term in terms:
           stripped = term.strip()
           if stripped and stripped not in seen:
               seen.add(stripped)
               result.append(stripped)
       return result

   # After
   def _process_terms(self, terms: list[str]) -> list[str]:
       return list(dict.fromkeys(t.strip() for t in terms if t.strip()))
   ```

2. **Import文の外部化**
   - ファイル: `src/genglossary/term_extractor.py`
   - 行: `_filter_excluded_terms`メソッド、`_add_common_nouns_to_exclusion`メソッド内
   - 変更内容: 関数内のimportをファイル先頭に移動
   ```python
   # ファイル先頭に追加
   from genglossary.db.excluded_term_repository import (
       get_excluded_term_texts,
       bulk_add_excluded_terms,
   )
   ```

3. **`add_excluded_term`のRETURNING句使用**
   - ファイル: `src/genglossary/db/excluded_term_repository.py`
   - 行: `add_excluded_term`関数
   - 変更内容: INSERT後のSELECTを削除し、RETURNING句でIDを直接取得
   - 注意: SQLite 3.35以上が必要（環境確認後に実施）

#### フロントエンド

1. **`excludedTermApi`中間レイヤーの削除**
   - ファイル: `frontend/src/api/hooks/useExcludedTerms.ts`
   - 変更内容: `excludedTermApi`オブジェクトを削除し、フック内で直接`apiClient`を呼び出す

2. **イベントハンドラーのinline最適化**
   - ファイル: `frontend/src/pages/TermsPage.tsx`
   - 行: `handleAddTerm`, `handleAddExcludedTerm`等のハンドラー関数
   - 変更内容: 冗長な変数宣言を削減

### 優先度中（リファクタリング効果大）

#### バックエンド

1. **プロンプト生成ロジックの共通化**
   - ファイル: `src/genglossary/term_extractor.py`
   - 行: `_create_classification_prompt`, `_create_*_prompt`系メソッド（5つ）
   - 変更内容: `_wrap_and_format_context`ヘルパーを抽出

2. **スキーマとモデルの統合検討**
   - ファイル:
     - `src/genglossary/models/excluded_term.py`
     - `src/genglossary/api/schemas/excluded_term_schemas.py`
   - 変更内容: `ExcludedTermResponse`を`ExcludedTerm`の継承または`model_validate`使用に変更

#### フロントエンド

1. **TermsPageのタブ分割**
   - ファイル: `frontend/src/pages/TermsPage.tsx`
   - 変更内容: `TermsTab.tsx`と`ExcludedTermsTab.tsx`に分割
   - 新規ファイル:
     - `frontend/src/components/terms/TermsTab.tsx`
     - `frontend/src/components/terms/ExcludedTermsTab.tsx`

2. **モーダルコンポーネント抽出**
   - ファイル: `frontend/src/pages/TermsPage.tsx`
   - 変更内容: Add Term / Add Excluded Termモーダルを共通コンポーネントに抽出
   - 新規ファイル: `frontend/src/components/terms/AddTermModal.tsx`

### 優先度低（アーキテクチャ変更）

1. **OpenAPI型定義からTypeScript型の自動生成**
   - 影響ファイル: `frontend/src/api/types.ts`
   - ツール: `openapi-typescript`等

2. **バリデーションライブラリの統一**
   - 影響ファイル:
     - `src/genglossary/models/excluded_term.py`
     - `src/genglossary/api/schemas/excluded_term_schemas.py`
     - `frontend/src/pages/TermsPage.tsx`

## Tasks

- [ ] `src/genglossary/term_extractor.py`: `_process_terms`を`dict.fromkeys`で簡素化
- [ ] `src/genglossary/term_extractor.py`: import文を関数外に移動
- [ ] `frontend/src/api/hooks/useExcludedTerms.ts`: `excludedTermApi`中間レイヤーを削除
- [ ] Commit
- [ ] Run tests (`uv run pytest` & `pnpm test`)

## Notes

- 機能的な問題はなく、コード品質改善のためのリファクタリング
- 削減見込み: バックエンド約150-200行、フロントエンド約100-150行
