---
priority: 7
tags: [refactoring, code-quality]
description: "Follow-up: Progress callback code quality improvements"
created_at: "2026-01-30T09:30:00Z"
started_at: null
closed_at: null
---

# Follow-up: Progress callback code quality improvements

## 概要

チケット `260130-refactor-progress-callback-improvements` のコードレビューで特定された、
中優先度以下の改善項目をまとめたフォローアップチケット。

## 対応項目

### Code Simplification

1. **重複したコールバック処理パターンの共通化**
   - 場所: `glossary_generator.py`, `glossary_refiner.py`
   - 両方で同じ try-except パターンが繰り返されている
   - 共通ヘルパー関数 `invoke_progress_callbacks()` への抽出を検討

2. **`_log` メソッドの簡略化**
   - 場所: `executor.py`
   - 辞書内包表記を使用してより簡潔に書ける

### Code Quality Issues (Backend)

3. **`conn` 未使用パラメータの対応**
   - 場所: `executor.py:_create_progress_callback`
   - 選択肢:
     - A) DB進捗更新を実装（`update_run_progress` を使用）
     - B) パラメータを削除（進捗はSSEログのみで十分な場合）
   - UIがポーリングに依存しているかSSEのみかを確認して判断

4. **`_log` の run_id=None 処理**
   - `execute` が run_id なしで呼ばれると `run_id: None` がログに含まれる
   - フィルタリング/表示の問題になる可能性
   - `run_id is None` の場合はフィールドを省略することを検討

5. **空の term_name メッセージフォーマット**
   - `term_name=""` の場合、`: 0%` というメッセージになる
   - フォールバックラベルを使用するか、`current_term` を省略することを検討

### Code Quality Issues (Frontend)

6. **グローバルログ状態のプロジェクト衝突**
   - 場所: `logStore.ts:11`, `useLogStream.ts:41`
   - runId のみでキーイングしているため、異なるプロジェクトで同じ runId があると衝突
   - 対策: `(projectId, runId)` でキーイング

7. **`run_id` の型不整合**
   - バックエンド: None の可能性
   - フロントエンド: 必須
   - 対策: 型定義の統一

8. **`runId = 0` の falsy 問題**
   - 場所: `useLogStream.ts:46`
   - `if (!runId)` で 0 が "no run" 扱い
   - 対策: `runId === undefined` に変更

9. **`onComplete` の stale closure**
   - 場所: `useLogStream.ts:67`
   - 依存配列に含まれていない
   - 対策: 依存配列に追加

## Tasks

- [ ] 優先度に基づいて対応を決定
- [ ] テストを追加・更新
- [ ] 実装
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## Notes

- 機能には影響しないコード品質改善
- 緊急性は低い
