---
priority: 3
tags: [improvement, backend, executor, refactoring]
description: "PipelineExecutor: Reduce duplicated cancellation check pattern"
created_at: "2026-01-30T20:50:00Z"
started_at: 2026-01-31T12:58:58Z
closed_at: null
---

# PipelineExecutor: Reduce duplicated cancellation check pattern

## 概要

各ステップ前で繰り返される `if self._check_cancellation(): return` パターンを DRY 原則に従って統一する。

## 現状の問題

**問題箇所**: `executor.py` 全体で10箇所

```python
if self._check_cancellation():
    return
```

このパターンが各ステップの前で繰り返されており、冗長。

## 提案する解決策

### オプション1: デコレータパターン

```python
def cancellable(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if self._check_cancellation():
            return
        return func(self, *args, **kwargs)
    return wrapper

@cancellable
def _execute_full(self, conn, doc_root):
    ...
```

### オプション2: ステップ実行ヘルパー

```python
def _run_step(self, step_func, *args, **kwargs):
    if self._check_cancellation():
        return False
    step_func(*args, **kwargs)
    return True
```

## 影響範囲

- `src/genglossary/runs/executor.py`

## Tasks

- [x] 設計選択 (デコレータパターンを採用)
- [x] 実装
- [x] テスト更新
- [x] Commit
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Update docs/architecture/*.md
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## Summary

### 設計決定
**オプション1: デコレータパターン** を採用。理由:
- メソッドエントリーでのキャンセルチェックを統一的に処理できる
- コードの重複を最小限に抑えられる
- 既存のテストが継続してパスする（振る舞いを維持）

### 実装内容
1. `_cancellable` デコレータを追加
   - ExecutionContext を引数から自動検出
   - キャンセル時は None を返して早期終了
2. 3つのメソッドにデコレータを適用
   - `_execute_full`
   - `_execute_from_terms`
   - `_execute_provisional_to_refined`
3. 5つの冗長なチェックを削除
   - 各メソッドのエントリーレベルチェック
   - ロード処理前のチェック（デコレータでカバー）
4. LLM呼び出し・保存前のチェックは維持（レスポンシブなキャンセルのため）

### 結果
- **Before**: 11 explicit checks
- **After**: 6 explicit checks + 3 decorator-handled checks
- テスト追加: 3 tests for decorator behavior (50 tests total)
- 全904テストパス、pyright エラーなし

### レビュー結果
- **code-simplifier**: scope処理は既存チケット `260130-executor-scope-strategy.md` でカバー
- **Codex**: 正常使用では問題なし。エッジケース（context不在）は理論的な問題のみ

## Notes

- code-simplifier レビューで指摘
- 優先度低：機能的には問題なし、保守性の改善
