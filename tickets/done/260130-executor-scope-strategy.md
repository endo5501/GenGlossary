---
priority: 4
tags: [improvement, backend, executor, refactoring]
description: "PipelineExecutor: Replace if-elif chain with Strategy pattern for scope handling"
created_at: "2026-01-30T20:50:00Z"
started_at: 2026-02-01T08:08:43Z
closed_at: 2026-02-01T08:24:07Z
---

# PipelineExecutor: Strategy pattern for scope handling

## 概要

スコープごとの実行ロジックを if-elif チェーンから Strategy パターンまたはディスパッチテーブルに変更し、拡張性を向上させる。

## 現状の問題

**問題箇所**: `executor.py:231-239`

```python
if scope_value == PipelineScope.FULL.value:
    self._execute_full(conn, doc_root)
elif scope_value == PipelineScope.FROM_TERMS.value:
    self._execute_from_terms(conn)
elif scope_value == PipelineScope.PROVISIONAL_TO_REFINED.value:
    self._execute_provisional_to_refined(conn)
else:
    self._log("error", f"Unknown scope: {scope_value}")
```

- Enum を使用しているのに文字列比較
- 新しいスコープ追加時に複数箇所の修正が必要

## 採用する設計

**選択**: ディスパッチテーブル + Enum キー + 統一シグネチャ + 直接メソッド参照

### 1. テーブルクリア関数のディスパッチテーブル（Enum キー）

```python
_SCOPE_CLEAR_FUNCTIONS: dict[PipelineScope, list[Callable[[sqlite3.Connection], None]]] = {
    PipelineScope.FULL: [delete_all_terms, delete_all_provisional, delete_all_issues, delete_all_refined],
    PipelineScope.FROM_TERMS: [delete_all_provisional, delete_all_issues, delete_all_refined],
    PipelineScope.PROVISIONAL_TO_REFINED: [delete_all_issues, delete_all_refined],
}
```

### 2. execute メソッドのスコープハンドラー（直接メソッド参照）

```python
def execute(self, conn, scope, context, doc_root="."):
    scope_enum = scope if isinstance(scope, PipelineScope) else PipelineScope(scope)

    self._clear_tables_for_scope(conn, scope_enum)

    # ローカルディスパッチテーブル（直接メソッド参照で型安全）
    scope_handlers = {
        PipelineScope.FULL: self._execute_full,
        PipelineScope.FROM_TERMS: self._execute_from_terms,
        PipelineScope.PROVISIONAL_TO_REFINED: self._execute_provisional_to_refined,
    }

    handler = scope_handlers.get(scope_enum)
    if handler is None:
        raise ValueError(f"Unknown scope: {scope_enum}")

    handler(conn, context, doc_root)
```

### 3. 関連メソッドの変更

- `_clear_tables_for_scope`: 引数の型を `str` から `PipelineScope` に変更
- `_execute_from_terms`, `_execute_provisional_to_refined`: `_doc_root` 引数を追加（統一シグネチャ、`_` プレフィックスで未使用を明示）

## 影響範囲

- `src/genglossary/runs/executor.py`

## Tasks

- [x] 設計選択
- [x] 実装
- [x] テスト更新
- [x] Commit
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Update docs/architecture/*.md
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing

## Notes

- code-simplifier レビューで指摘
- 優先度低：現状で機能的には問題なし
