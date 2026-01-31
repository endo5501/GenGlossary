---
priority: 4
tags: [enhancement, backend, race-condition]
description: "RunManager: Handle late-cancel race condition"
created_at: "2026-01-31T10:00:00+09:00"
started_at: null
closed_at: null
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

## Tasks

- [ ] ユーザー体験の観点から望ましい動作を決定
- [ ] 選択した方針に基づいて実装
- [ ] テストの追加
