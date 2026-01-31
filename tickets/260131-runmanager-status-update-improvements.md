---
priority: 3
tags: [refactoring, backend, code-quality]
description: "RunManager: Improve status update fallback logic"
created_at: "2026-01-31T16:00:00+09:00"
started_at: null
closed_at: null
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

- [ ] no-op と失敗を区別するロジックの設計
- [ ] 例外ハンドリングの改善
- [ ] `_try_cancel_status` の戻り値確認
- [ ] （オプション）共通トランザクション処理ロジックの抽出
- [ ] テストの追加/更新
- [ ] Commit
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing
