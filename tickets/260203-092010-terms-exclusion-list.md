---
priority: 3
tags: [backend, frontend, database, performance]
description: "除外用語一覧を追加し、用語抽出の効率化とユーザー制御を実現"
created_at: "2026-02-03T09:20:10Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# 除外用語一覧機能の追加

## 概要

### 現状の問題

現在の用語抽出フローには以下の非効率性がある：

1. **毎回のLLM再分類**: SudachiPyで形態素解析した結果を毎回LLMで分類している
2. **common_nounの再処理**: 一度`common_noun`に分類された用語も、ファイル追加・更新時に再度LLMで分類される
3. **手動除外不可**: `common_noun`以外にも除外したい用語があっても、ユーザーが制御できない

### 現在のフロー
```
SudachiPy形態素解析 → 全候補をLLMで分類 → common_noun除外 → 用語一覧
                      ↑ 毎回すべて再分類（非効率）
```

### 提案するフロー
```
SudachiPy形態素解析 → 除外用語一覧でフィルタ → 残りをLLMで分類 → common_noun → 除外用語一覧に自動追加
                      ↑ 既知の除外用語はスキップ（効率的）          ↓
                                                              用語一覧
```

## 機能要件

### 1. 除外用語一覧テーブル
- 用語テキスト（一意）
- 追加元（auto: LLMがcommon_nounに分類 / manual: ユーザーが手動追加）
- 追加日時

### 2. 自動追加
- LLMが`common_noun`に分類した用語は自動的に除外用語一覧に追加
- 既存の`common_noun`分類ロジックと連携

### 3. 手動管理
- ユーザーが任意の用語を除外用語一覧に追加可能
- 除外用語一覧から用語を削除可能（再分類対象に戻す）
- Terms画面から直接追加（用語を選択して「除外」ボタン）

### 4. 抽出時のフィルタリング
- SudachiPy結果から除外用語一覧にある用語を事前に除外
- LLMへの分類リクエスト数を削減

## 現状分析

### 関連ファイル（バックエンド）
- `src/genglossary/db/schema.py` - DBスキーマ定義（SCHEMA_VERSION=4）
- `src/genglossary/term_extractor.py` - 用語抽出ロジック（`_classify_terms`, `_select_terms`）
- `src/genglossary/morphological_analyzer.py` - SudachiPy形態素解析
- `src/genglossary/models/term.py` - `TermCategory.COMMON_NOUN` enum定義
- `src/genglossary/db/term_repository.py` - 用語のDB操作
- `src/genglossary/api/routers/terms.py` - Terms API

### 関連ファイル（フロントエンド）
- `frontend/src/pages/TermsPage.tsx` - Terms画面
- `frontend/src/api/hooks/useTerms.ts` - 用語関連フック

## Tasks

### Phase 1: データベース拡張
- [ ] `terms_excluded` テーブルをスキーマに追加（SCHEMA_VERSION=5）
  - `id`: INTEGER PRIMARY KEY
  - `term_text`: TEXT NOT NULL UNIQUE
  - `source`: TEXT NOT NULL ('auto' | 'manual')
  - `created_at`: TEXT NOT NULL
- [ ] マイグレーション処理の追加
- [ ] `excluded_term_repository.py` の作成（CRUD操作）

### Phase 2: バックエンドAPI
- [ ] `/api/projects/{project_id}/excluded-terms` エンドポイント追加
  - `GET`: 除外用語一覧取得
  - `POST`: 除外用語追加（手動）
  - `DELETE /{term_id}`: 除外用語削除
- [ ] スキーマ定義（`ExcludedTermResponse`, `ExcludedTermCreateRequest`）

### Phase 3: 用語抽出ロジック改修
- [ ] `TermExtractor._classify_terms()` の前に除外用語フィルタを追加
- [ ] `common_noun` 分類時に除外用語一覧へ自動追加
- [ ] フィルタリング統計情報の追加（スキップ数など）

### Phase 4: フロントエンドUI
- [ ] `useExcludedTerms` フック作成
- [ ] Terms画面に除外用語一覧セクション追加
  - テーブル表示（用語、追加元、追加日時）
  - 削除ボタン
- [ ] 用語を除外用語一覧に追加するUI
  - 用語詳細パネルに「除外に追加」ボタン
  - または用語行にコンテキストメニュー
- [ ] 手動で除外用語を追加するモーダル

### Phase 5: 統合・テスト
- [ ] E2Eテスト追加
- [ ] パフォーマンス改善の検証

### 品質タスク
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

### スコープの分割案

このチケットは大きいため、以下のように分割することも検討：

1. **Ticket A**: DB + Backend API（Phase 1-2）
2. **Ticket B**: 用語抽出ロジック改修（Phase 3）
3. **Ticket C**: フロントエンドUI（Phase 4）

### 設計上の検討事項

1. **プロジェクト単位 vs グローバル**:
   - 現在の設計ではプロジェクト単位で用語を管理
   - 除外用語もプロジェクト単位が自然
   - テーブルには `project_id` カラムを含めるべき

2. **既存データの移行**:
   - 既に`common_noun`に分類された用語がある場合の扱い
   - 移行スクリプトで一括追加するか、次回抽出時に自動追加するか

3. **UI/UX**:
   - 除外用語一覧を別タブにするか、Terms画面内のセクションにするか
   - 用語と除外用語の表示切り替え

### パフォーマンス期待値

- 一度分類した`common_noun`は再分類不要
- ファイル更新時のLLM APIコール数が大幅削減
- 大量ドキュメントでの抽出時間短縮
