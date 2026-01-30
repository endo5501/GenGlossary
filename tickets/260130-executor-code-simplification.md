---
priority: 1
tags: [refactoring, backend, code-quality]
description: "PipelineExecutor: Code simplification and DRY improvements"
created_at: "2026-01-30T10:20:00Z"
started_at: null
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

- [ ] 設計検討
- [ ] テスト確認（既存テストが全てパスすることを確認）
- [ ] ヘルパーメソッド抽出
- [ ] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [ ] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket.
- [ ] Code review by codex MCP. If the issue is not addressed immediately, create a ticket.
- [ ] Update docs/architecture/*.md
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## Notes

- 260130-log-state-architecture チケットのレビューで発見
- 機能変更なし、リファクタリングのみ
