---
priority: 4
tags: [improvement, backend, executor, refactoring]
description: "PipelineExecutor: Replace if-elif chain with Strategy pattern for scope handling"
created_at: "2026-01-30T20:50:00Z"
started_at: null
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

## 提案する解決策

### オプション1: ディスパッチテーブル

```python
_SCOPE_HANDLERS = {
    PipelineScope.FULL: "_execute_full",
    PipelineScope.FROM_TERMS: "_execute_from_terms",
    PipelineScope.PROVISIONAL_TO_REFINED: "_execute_provisional_to_refined",
}

def execute(self, ...):
    handler = getattr(self, self._SCOPE_HANDLERS[scope])
    handler(conn, ...)
```

### オプション2: Enum にメソッド参照を持たせる

```python
class PipelineScope(Enum):
    FULL = ("full", "_execute_full")
    ...
```

## 影響範囲

- `src/genglossary/runs/executor.py`

## Tasks

- [ ] 設計選択
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
