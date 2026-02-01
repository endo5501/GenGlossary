---
priority: 4
tags: [enhancement, backend, race-condition]
description: "RunManager: Handle late-cancel race condition"
created_at: "2026-01-31T10:00:00+09:00"
started_at: 2026-02-01T09:04:07Z
closed_at: 2026-02-01T09:34:44Z
---

# RunManager: Handle late-cancel race condition

## 概要

codex MCP レビューで指摘された問題。パイプライン完了後にキャンセルリクエストが到着した場合の処理について、設計上の決定が必要。

## 問題の詳細

`_finalize_run_status` でパイプライン完了後に `cancel_event.is_set()` をチェックし、true の場合は `cancel_run` を呼び出している。これにより以下のシナリオが発生する可能性がある：

1. パイプラインが正常に完了
2. `_finalize_run_status` が呼ばれる前にキャンセルリクエストが到着
3. `cancel_event.is_set()` が true になる
4. `cancel_run` が呼ばれ、ステータスが `cancelled` になる

パイプラインは実際には正常に完了しているが、ステータスは `cancelled` として表示される。

## 検討すべき選択肢

1. **現状維持**: キャンセルリクエストがあれば常に `cancelled` を優先
   - ユーザーの明示的なキャンセル操作を尊重
   - ただし、結果が失われる可能性

2. **完了を優先**: パイプライン完了後のキャンセルは無視
   - executor から「キャンセルされたか」フラグを返す
   - パイプラインが実際に途中で停止した場合のみ `cancelled`

3. **DBステータスを確認**: `cancel_run_if_still_running` のような条件付き更新
   - `complete_run_if_not_cancelled` と同様のアトミック操作

## 関連ファイル

- `src/genglossary/runs/manager.py:315`
- `src/genglossary/runs/manager.py:349`

## 設計決定

### 方針: 完了を優先

パイプラインが実際に完了していれば `completed` として結果を保持する。キャンセルリクエストが間に合わなかった場合は、キャンセルは無視される。

**理由**: ユーザーの成果物（用語集）が失われないことを優先。

### 実装方法: パイプラインから結果を返す

`executor.execute()` が「キャンセルによって中断されたか」を示す bool を返すように変更。

### 変更箇所

1. **executor.py**
   - `execute()` の戻り値を `None` → `bool` に変更
   - `True`: キャンセルで中断された
   - `False`: 正常完了
   - 各所の `return` を `return True` に、最後に `return False` を追加

2. **manager.py**
   - `execute()` の戻り値を `was_cancelled` として受け取る
   - `_finalize_run_status` のシグネチャ変更: `cancel_event: Event` → `was_cancelled: bool`
   - 判定ロジックを `cancel_event.is_set()` から `was_cancelled` に変更

### テストシナリオ

1. 正常完了（キャンセルなし）→ `completed`
2. キャンセルで中断 → `cancelled`
3. 遅延キャンセル（完了後にキャンセルリクエスト）→ `completed`（今回の修正対象）
4. パイプラインエラー → `failed`（既存動作、変更なし）

## Tasks

- [x] ユーザー体験の観点から望ましい動作を決定
- [x] 選択した方針に基づいて実装
- [x] テストの追加
- [x] Commit
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Update docs/architecture/*.md
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing
