---
priority: 1
tags: [refactor, backend, frontend]
description: "Reduce ~70% code duplication between excluded terms and required terms implementations"
created_at: "2026-02-07T11:09:19Z"
started_at: 2026-02-07T11:13:01Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# 除外用語/必須用語のコード重複削減リファクタリング

## 概要

excluded terms と required terms の実装間に約70%のコード重複がある。
コードレビュー（code-simplifier agent）により以下の改善ポイントが指摘された。

## 設計

### 1. バックエンド: 共通バリデータの抽出

- `models/term_validator.py` に共通バリデータ関数 `validate_term_text()` を作成
- 各モデル（ExcludedTerm, RequiredTerm）はこの関数を field_validator から呼び出す
- モデル自体は個別に残す（source の型が異なるため）

### 2. バックエンド: ジェネリックリポジトリ関数（関数ベース）

- `db/term_repository.py` に共通CRUD関数群を作成
- テーブル名・モデル型をパラメータで受け取る
- 対象関数: add_term, delete_term, get_all_terms, get_term_by_id, term_exists, get_term_texts, bulk_add_terms
- 既存の excluded_term_repository.py / required_term_repository.py は薄いラッパーとして残す

### 3. バックエンド: APIスキーマの共通化

- `schemas/term_schemas.py` に共通レスポンス・リクエストモデルを作成
- 既存スキーマファイルはエイリアス/継承として残す
- ルーターは個別に残す（URLパスが異なるため）

### 4. フロントエンド: 共通フック

- `api/hooks/useTermsCrud.ts` にジェネリックフックを作成
- apiPath, queryKeyPrefix をパラメータで受け取る
- 既存の useExcludedTerms.ts / useRequiredTerms.ts は薄いラッパーとして残す

### 5. フロントエンド: 共通UIコンポーネント

- `components/AddTermModal.tsx`: 共通モーダル（title, onSubmit 等を props で制御）
- `components/TermListTable.tsx`: 共通テーブル（columns config で Source 列の有無を制御）
- TermsPage では props の違いのみで2つのテーブル/モーダルを描画


## Tasks

- [ ] バックエンド: 共通バリデータの抽出 (models/term_validator.py)
- [ ] バックエンド: ジェネリックリポジトリ関数の抽出 (db/term_repository.py)
- [ ] バックエンド: APIスキーマの共通化 (schemas/term_schemas.py)
- [ ] フロントエンド: 共通フック (api/hooks/useTermsCrud.ts)
- [ ] フロントエンド: 共通 AddTermModal コンポーネント
- [ ] フロントエンド: 共通 TermListTable コンポーネント
- [ ] Commit
- [ ] Run static analysis (`pyright`) before reviewing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before reviewing and pass all tests (No exceptions)
- [ ] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Update docs/architecture/*.md
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing


## Notes

- リファクタリングのため機能変更なし。既存テストが全て通ることが必須
- 既存の個別ファイル（リポジトリ、フック等）は薄いラッパーとして残し、呼び出し側への影響を最小化
