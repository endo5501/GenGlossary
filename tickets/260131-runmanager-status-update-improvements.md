---
priority: 3
tags: [refactoring, backend, code-quality]
description: "RunManager: Improve status update fallback logic"
created_at: "2026-01-31T16:00:00+09:00"
started_at: 2026-01-31T14:24:05Z
closed_at: 2026-01-31T14:39:24Z
---

# RunManager: Improve status update fallback logic

## 概要

code-simplifier agent および codex MCP のレビューで指摘された問題。現在の `_try_status_with_fallback` メソッドと関連メソッドに改善の余地がある。

## 指摘された問題

### 1. `_try_complete_status` の no-op 時のフォールバック（Medium）

`_try_complete_status` が `False` を返すケースは2つある：
1. DB例外で失敗 → フォールバック試行は正しい
2. `complete_run_if_not_cancelled` が `False`（すでに終了状態）→ フォールバック試行は不要

現在のコードでは両方のケースでフォールバックが試行される。

**改善案**: no-op と失敗を区別する戻り値またはシグナルを導入

### 2. 例外ハンドリングの脆弱性（Medium）

`_try_status_with_fallback` は updater が例外を内部でキャッチすることを前提としている。将来の updater が例外を投げた場合、フォールバックパスが実行されない。

**改善案**: プライマリ接続の試行に try-except を追加

### 3. `_try_cancel_status` の戻り値（Low）

`cancel_run` が行を更新しなくても `True` を返すため、実際の失敗がマスクされる可能性がある。

**改善案**: `cancel_run` の戻り値を確認するか、別のシグナルを使用

### 4. さらなる簡素化の機会（code-simplifier agent）

- 共通トランザクション処理ロジックを `_try_status_update_with_transaction` に抽出
- `_try_update_status` を `_try_failed_status` に改名して一貫性を向上
- `_finalize_run_status` の簡素化

## 関連ファイル

- `src/genglossary/runs/manager.py`

## Tasks

- [x] no-op と失敗を区別するロジックの設計
- [x] 例外ハンドリングの改善
- [x] `_try_cancel_status` の戻り値確認
- [x] （オプション）`_try_update_status` を `_try_failed_status` に改名
- [x] テストの追加/更新
- [x] Commit
- [x] Run static analysis (`pyright`) before reviewing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest`) before reviewing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Update docs/architecture/*.md
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing

## レビュー結果

### code-simplifier agent

共通パターンの抽出を提案：
- `_try_complete_status`, `_try_cancel_status`, `_try_failed_status` の3メソッドに重複パターンあり
- 共通の `_try_status_update` メソッドに統合可能
- コード行数を約50%削減できる見込み

→ 今回は軽微な改善（メソッド名の一貫性向上）のみ実施。共通化は将来の改善として検討可能。

### codex MCP

**High**: `_try_failed_status` が終了状態を上書きする可能性
- 他のスレッドが先に cancel/complete を設定した場合、failed で上書きされる
- cancel/complete と同様の条件付き更新が必要

→ 新規チケット作成: `tickets/260131-143402-runmanager-failed-status-guard.md`

**Medium**: `cancel_run` の rowcount 0 が「終了状態」と「存在しない」を区別できない
- 現時点では許容範囲（run は削除されない前提）

**Low**: フォールバック失敗時のログが不十分
- 現時点では各 updater がログを出力しているため問題なし
