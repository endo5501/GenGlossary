---
priority: 5
tags: [enhancement, backend, robustness]
description: "RunManager: Handle cancellation exceptions distinctly"
created_at: "2026-01-31T10:05:00+09:00"
started_at: 2026-02-01T10:50:57Z
closed_at: null
---

# RunManager: Handle cancellation exceptions distinctly

## 概要

codex MCP レビューで指摘された問題。現在の実装では、executor がキャンセル時に例外を投げた場合、`cancelled` ではなく `failed` としてマークされる可能性がある。

## 問題の詳細

`_finalize_run_status` では `pipeline_error` の有無を最初にチェックし、エラーがあれば `failed` ステータスに更新する。これにより以下の問題が発生する可能性がある：

1. ユーザーがキャンセルをリクエスト
2. executor がキャンセルを検出し、`CancellationError` のような例外を投げる
3. `_finalize_run_status` が `pipeline_error` を検出
4. `cancel_event.is_set()` をチェックする前に `failed` ステータスに更新

## 現在の動作

現在の PipelineExecutor はキャンセル時に例外を投げず、単に早期リターンするため、この問題は発生しない。しかし、将来の変更に備えて対応することが推奨される。

## 提案される解決策

1. **キャンセル例外クラスの導入**:
   ```python
   class PipelineCancelledException(Exception):
       pass
   ```

2. **_finalize_run_status でのチェック**:
   ```python
   if pipeline_error is not None:
       if isinstance(pipeline_error, PipelineCancelledException):
           # キャンセルとして処理
           ...
       else:
           # エラーとして処理
           ...
   ```

3. **executor からの明示的なフラグ**:
   - executor が `was_cancelled` フラグを返す方式

## 関連ファイル

- `src/genglossary/runs/manager.py:299`
- `src/genglossary/runs/executor.py`

---

## 実装設計（2026-02-01 承認済み）

### 1. 例外クラスの定義

**ファイル**: `src/genglossary/runs/executor.py`

```python
class PipelineCancelledException(Exception):
    """Raised when pipeline execution is cancelled by user request."""
    pass
```

- `ExecutionContext` クラスの前に配置

### 2. executor の変更

**ファイル**: `src/genglossary/runs/executor.py`

- `_check_cancellation` メソッド: `bool` を返す代わりに `PipelineCancelledException` を raise
- `@_cancellable` デコレータ: `return True` の代わりに例外を raise
- `execute()` と各 `_execute_*` メソッド: `if self._check_cancellation(): return True` パターンを削除し簡素化

### 3. manager の変更

**ファイル**: `src/genglossary/runs/manager.py`

- `_finalize_run_status` から `was_cancelled` 引数を削除
- `pipeline_error` が `PipelineCancelledException` かどうかで `cancelled` / `failed` を判定
- `_execute_run` から `was_cancelled` 変数を削除
- import 追加: `from genglossary.runs.executor import PipelineCancelledException`

### 4. テスト戦略

- executor が `PipelineCancelledException` を raise することを確認
- manager が例外を `cancelled` ステータスに変換することを確認
- 通常の例外は `failed` ステータスになることを確認（回帰テスト）
- 既存テストを例外ベースに更新

---

## Tasks

- [ ] キャンセル例外クラスまたはフラグの設計
- [ ] executor の修正（必要な場合）
- [ ] _finalize_run_status の修正
- [ ] テストの追加
- [ ] Commit
- [ ] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest`) before reviwing and pass all tests (No exceptions)
- [ ] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Update docs/architecture/*.md
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing
