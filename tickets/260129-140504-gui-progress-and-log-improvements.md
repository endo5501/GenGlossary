---
priority: 3
tags: [enhancement, gui, ux]
description: "GUI: 進捗表示とログ保持の改善"
created_at: "2026-01-29T14:05:04Z"
started_at: 2026-01-29T22:27:18Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# GUI: 進捗表示とログ保持の改善

## 概要

現在のGUIでは処理の進捗がわかりにくく、ページを切り替えるとログが消えてしまう問題がある。

## 問題点

### 1. 進捗表示の不足

- 処理中の進捗率が表示されない
- どのステップを実行中かわかりにくい
- 完了までの目安がわからない

### 2. ログの揮発性

- ページを切り替えるとログ表示がクリアされる
- 現在の状況がわからなくなる
- エラー発生時のデバッグが困難

## 期待される動作

### 進捗表示

- ログ表示に進捗率と処理中の用語を表示（例: "Ollama":25%, "大規模言語モデル":50%, "qwen3":75%, "API":100%）
- 現在のステップをログに明示（例: "Step 2/5: Generating glossary..."）

### ログ保持

- ページを切り替えてもログが保持される
- 再解析時、前回のログはクリアする

### ログ保持

- React Context または Zustand でログ状態を管理
- プロジェクト単位でログを保持

## Tasks

- [x] 進捗表示の設計
- [x] バックエンドの処理中情報送信を実装
- [x] ログ状態管理の実装
- [ ] playwright MCPを使用してログに解析中の用語が表示されることを確認
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [ ] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket.
- [ ] Code review by codex MCP. If the issue is not addressed immediately, create a ticket.
- [ ] Update docs/architecture/*.md
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## Implementation Summary

### Phase 1: バックエンド進捗更新

**変更ファイル:**
- `src/genglossary/runs/executor.py`
- `src/genglossary/types.py`

**内容:**
- `_create_progress_callback()` メソッドを追加
- `_log()` を拡張して `step`, `progress_current`, `progress_total`, `current_term` をサポート
- `TermProgressCallback` 型を追加

### Phase 2: コンポーネント統合

**変更ファイル:**
- `src/genglossary/glossary_generator.py`
- `src/genglossary/glossary_refiner.py`
- `src/genglossary/runs/executor.py`

**内容:**
- `GlossaryGenerator.generate()` に `term_progress_callback` パラメータを追加
- `GlossaryRefiner.refine()` に `term_progress_callback` パラメータを追加
- executor から progress callback を生成して各コンポーネントに渡す

### Phase 3: フロントエンド状態管理（Zustand）

**変更ファイル:**
- `frontend/src/store/logStore.ts` (新規)
- `frontend/src/api/hooks/useLogStream.ts`
- `frontend/src/api/types.ts`

**内容:**
- Zustand をインストール (`pnpm add zustand`)
- `logStore` を作成してログをグローバルに管理
- `useLogStream` を Zustand ストアと統合
- `LogMessage` 型に進捗フィールドを追加

### Phase 4: UI改善（進捗表示）

**変更ファイル:**
- `frontend/src/components/layout/LogPanel.tsx`
- `frontend/src/store/logStore.ts`

**内容:**
- `latestProgress` 状態を logStore に追加
- LogPanel にプログレスバーを表示
- 現在のステップ名と処理中の用語名を表示
- current/total カウントを表示

## Notes

- 優先度は低め（機能改善）
- バグ修正後に対応
