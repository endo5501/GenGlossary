---
priority: 5
tags: [enhancement, backend, robustness]
description: "RunManager: Handle cancellation exceptions distinctly"
created_at: "2026-01-31T10:05:00+09:00"
started_at: null
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

## Tasks

- [ ] キャンセル例外クラスまたはフラグの設計
- [ ] executor の修正（必要な場合）
- [ ] _finalize_run_status の修正
- [ ] テストの追加
- [ ] Commit
- [ ] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest`) before reviwing and pass all tests (No exceptions)
- [ ] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket.
- [ ] Code review by codex MCP. If the issue is not addressed immediately, create a ticket.
- [ ] Update docs/architecture/*.md
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing
