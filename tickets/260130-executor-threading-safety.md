---
priority: 1
tags: [improvement, backend, threading, architecture]
description: "PipelineExecutor: Threading safety improvements"
created_at: "2026-01-30T20:40:00Z"
started_at: null
closed_at: null
---

# PipelineExecutor: Threading safety improvements

## 概要

PipelineExecutor のスレッドセーフティに関する問題を解決する。

## 現状の問題

### 1. SQLite 接続のスレッド安全性

**問題箇所**: `executor.py:49-67, 194-236`

PipelineExecutor はバックグラウンドスレッドで実行されるが、呼び出し元から渡された `sqlite3.Connection` を使用している。SQLite は同じ接続を異なるスレッドで使用することを禁止している（`check_same_thread` が True の場合）。

**現状の対策**: `connection.py` で `check_same_thread=False` を設定済み

**残るリスク**: 接続が別スレッドで作成された場合、まれに問題が発生する可能性

### 2. インスタンス状態のスレッド安全性

**問題箇所**: `executor.py:63-67, 214-218`

```python
self._run_id = run_id
self._log_callback = log_callback
self._cancel_event = cancel_event
```

同一の `PipelineExecutor` インスタンスで複数の `execute()` を並行呼び出しすると、インスタンス変数が上書きされ、ログやキャンセル信号が混在する。

**影響**:
- ログが間違った run_id で記録される
- キャンセル信号が別の実行に影響する

## 提案する解決策

### オプション1: 実行ごとに新規インスタンス

`RunManager` で毎回新しい `PipelineExecutor` インスタンスを作成。

```python
def _run_pipeline(self, ...):
    executor = PipelineExecutor(...)  # 毎回新規
    executor.execute(...)
```

**メリット**: 最もシンプル、状態分離が保証される
**デメリット**: LLM クライアントの再作成コスト

### オプション2: 実行コンテキストオブジェクト

インスタンス状態を実行コンテキストとして分離。

```python
@dataclass
class ExecutionContext:
    run_id: int
    log_callback: Callable
    cancel_event: Event

def execute(self, context: ExecutionContext, ...):
    # self._xxx の代わりに context.xxx を使用
```

**メリット**: LLM クライアントを再利用可能
**デメリット**: API 変更が必要

### オプション3: スレッドローカル変数

`threading.local()` を使用して、スレッドごとに状態を分離。

**メリット**: API 変更なし
**デメリット**: 実装が複雑

## 影響範囲

- `src/genglossary/runs/executor.py`
- `src/genglossary/runs/manager.py`
- テスト

## Tasks

- [ ] 設計レビュー・承認
- [ ] 実装
- [ ] テストの更新（並行実行テストの追加）
- [ ] Commit
- [ ] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [ ] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket.
- [ ] Code review by codex MCP. If the issue is not addressed immediately, create a ticket.
- [ ] Update docs/architecture/*.md
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## Notes

- 260130-executor-improvements チケットから延期
- codex MCP レビューで Medium 優先度として指摘
- 現状 RunManager は1プロジェクトで1アクティブRunのみ許可しているため、実際には問題が顕在化しにくい
