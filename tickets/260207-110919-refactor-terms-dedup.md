---
priority: 1
tags: [refactor, backend, frontend]
description: "Reduce ~70% code duplication between excluded terms and required terms implementations"
created_at: "2026-02-07T11:09:19Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# 除外用語/必須用語のコード重複削減リファクタリング

## 概要

excluded terms と required terms の実装間に約70%のコード重複がある。
コードレビュー（code-simplifier agent）により以下の改善ポイントが指摘された。

## 改善ポイント

### 1. バックエンド: ジェネリックリポジトリパターン

`excluded_term_repository.py` と `required_term_repository.py` が同一パターンのCRUD関数を重複実装している。
共通の base repository を抽出してジェネリック化する。

### 2. バックエンド: バリデータの共有

`ExcludedTerm` と `RequiredTerm` モデルの `term_text` バリデータが同一。
共通バリデータの抽出を検討する。

### 3. フロントエンド: UIコンポーネントの抽出

TermsPage 内の除外用語テーブルと必須用語テーブルの構造がほぼ同一。
共通コンポーネント（TermsTable, AddTermModal）を抽出する。

### 4. フロントエンド: フックの共通化

`useExcludedTerms.ts` と `useRequiredTerms.ts` の構造が同一。
ジェネリックフックの検討。


## Tasks

- [ ] バックエンド: ジェネリックリポジトリ関数の抽出
- [ ] バックエンド: 共通バリデータの抽出
- [ ] フロントエンド: 共通 TermsTable コンポーネントの抽出
- [ ] フロントエンド: 共通 AddTermModal コンポーネントの抽出
- [ ] フロントエンド: ジェネリックフックの検討・実装
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

- コード重複は機能に影響しないため、優先度3（低）で対応
- リファクタリング時は既存テストが全て通ることを確認
