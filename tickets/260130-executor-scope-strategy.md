---
priority: 4
tags: [improvement, backend, executor, refactoring]
description: "PipelineExecutor: Replace if-elif chain with Strategy pattern for scope handling"
created_at: "2026-01-30T20:50:00Z"
started_at: 2026-02-01T08:08:43Z
closed_at: null
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

**選択**: ディスパッチテーブル + Enum キー + 統一シグネチャ

### 1. ディスパッチテーブルの定義

```python
# 既存の _SCOPE_CLEAR_FUNCTIONS を Enum キーに変更
_SCOPE_CLEAR_FUNCTIONS: dict[PipelineScope, list[Callable[[sqlite3.Connection], None]]] = {
    PipelineScope.FULL: [delete_all_terms, delete_all_provisional, delete_all_issues, delete_all_refined],
    PipelineScope.FROM_TERMS: [delete_all_provisional, delete_all_issues, delete_all_refined],
    PipelineScope.PROVISIONAL_TO_REFINED: [delete_all_issues, delete_all_refined],
}

# 新規: スコープハンドラーのディスパッチテーブル
_SCOPE_HANDLERS: dict[PipelineScope, str] = {
    PipelineScope.FULL: "_execute_full",
    PipelineScope.FROM_TERMS: "_execute_from_terms",
    PipelineScope.PROVISIONAL_TO_REFINED: "_execute_provisional_to_refined",
}
```

### 2. execute メソッドの変更

```python
def execute(self, conn, scope, context, doc_root="."):
    # Enum に正規化（文字列の場合は変換）
    scope_enum = scope if isinstance(scope, PipelineScope) else PipelineScope(scope)

    self._log(context, "info", f"Starting pipeline execution: {scope_enum.value}")

    if self._check_cancellation(context):
        return

    self._clear_tables_for_scope(conn, scope_enum)

    # ディスパッチテーブルからハンドラーを取得
    handler_name = _SCOPE_HANDLERS.get(scope_enum)
    if handler_name is None:
        self._log(context, "error", f"Unknown scope: {scope_enum}")
        raise ValueError(f"Unknown scope: {scope_enum}")

    handler = getattr(self, handler_name)
    handler(conn, context, doc_root)

    self._log(context, "info", "Pipeline execution completed")
```

### 3. 関連メソッドの変更

- `_clear_tables_for_scope`: 引数の型を `str` から `PipelineScope` に変更
- `_execute_from_terms`, `_execute_provisional_to_refined`: `doc_root` 引数を追加（統一シグネチャ）

## 影響範囲

- `src/genglossary/runs/executor.py`

## Tasks

- [x] 設計選択
- [ ] 実装
- [ ] テスト更新
- [ ] Commit
- [ ] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [ ] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Update docs/architecture/*.md
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## Notes

- code-simplifier レビューで指摘
- 優先度低：現状で機能的には問題なし
