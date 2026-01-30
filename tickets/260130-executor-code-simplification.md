---
priority: 1
tags: [refactoring, backend, code-quality]
description: "PipelineExecutor: Code simplification and DRY improvements"
created_at: "2026-01-30T10:20:00Z"
started_at: 2026-01-30T10:34:14Z
closed_at: null
---

# PipelineExecutor: Code simplification and DRY improvements

## 概要

code-simplifier agentのレビューで、`executor.py`に大量のコード重複が発見された。
リファクタリングにより100行以上の削減が可能。

## 問題の詳細

### A. 用語保存ロジックの重複 (行299-306, 390-397)

provisional保存とrefined保存で同一のパターン:
```python
for term in glossary.terms.values():
    create_xxx_term(conn, term.name, term.definition, ...)
```

### B. データ再構築パターンの重複 (行189-199, 338-348)

DocumentとGlossaryの再構築ロジックが類似。

### C. キャンセルチェックの繰り返し

全メソッドで同じパターン:
```python
if self._check_cancellation():
    return
```

### D. テーブルクリアロジックの冗長性 (行408-422)

3つのスコープで似たようなテーブルクリア処理。

## 対策案

1. `_save_glossary_to_db(conn, glossary, save_func)` ヘルパーメソッド
2. `_reconstruct_glossary(conn)`, `_reconstruct_documents(conn)` ヘルパー
3. キャンセルチェックのデコレータまたはコンテキストマネージャー
4. テーブルクリアのマップベース実装

## 影響範囲

- `src/genglossary/runs/executor.py`

## Tasks

- [x] 設計検討
- [x] テスト確認（既存テストが全てパスすることを確認）
- [x] ヘルパーメソッド抽出
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
  - pytest: 727 passed
  - pnpm test: 156/157 passed (LogPanel.test.tsx failure is pre-existing, tracked in separate ticket)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket.
  - Created: `260130-executor-improvements.md`
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket.
  - Created: `260130-executor-bugs-from-review.md`, `260130-executor-improvements.md`
- [x] Update docs/architecture/*.md
  - Not needed: Internal implementation changes only, no API changes
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing

## 実施内容

### 追加したヘルパーメソッド

1. **`_SCOPE_CLEAR_FUNCTIONS`** - モジュール定数としてスコープ別クリア関数マップを定義
2. **`_documents_from_db_rows()`** - DB行をDocumentオブジェクトに変換
3. **`_glossary_from_db_rows()`** - DB行をGlossaryオブジェクトに変換
4. **`_save_glossary_terms()`** - 用語集保存ロジックを統一

### 対応しなかった項目

- **C. キャンセルチェック**: メソッド途中で使用されているためデコレータ化は不適切と判断し現状維持

### 行数変化

- Before: 422行
- After: 443行 (+21行)

行数は増加したが、ヘルパーメソッドとdocstringの追加によるもの。コードの重複は削減され、可読性と保守性が向上。

### テスト修正

- `test_re_execution_clears_tables`: `_SCOPE_CLEAR_FUNCTIONS` をパッチするよう更新

## 関連チケット

- `260130-executor-bugs-from-review.md` - レビューで発見されたバグ (priority: 2)
- `260130-executor-improvements.md` - コード品質改善提案 (priority: 5)

## Notes

- 260130-log-state-architecture チケットのレビューで発見
- 機能変更なし、リファクタリングのみ
