---
priority: 4
tags: [refactoring, code-quality]
description: "Refactor: Progress callback handling improvements"
created_at: "2026-01-30T07:55:00Z"
started_at: 2026-01-30T09:17:28Z
closed_at: null
---

# Refactor: Progress callback handling improvements

## 概要

GUI進捗表示機能実装時のコードレビューで特定された改善点に対応する。

## Code Simplification (code-simplifier agent)

### 高優先度
1. **重複したプログレスコールバック呼び出しパターン**
   - 場所: `glossary_generator.py`, `glossary_refiner.py` (106-110行目)
   - 両方で同じパターンが繰り返されている
   - 共通関数への抽出を検討

### 中優先度
2. **不要な型エイリアス `ProgressCallback`**
   - 場所: `types.py`
   - `TermProgressCallback` に統一可能

3. **`_log` メソッドの複雑なパラメータ構築**
   - 場所: `executor.py` (52-82行目)
   - `**kwargs` を使用してより簡潔に書ける

### 低優先度
4. **未使用の `getLatestProgress` メソッド** - `logStore.ts`
5. **進捗計算ロジックの重複** - バックエンドとフロントエンド両方で計算
6. **`useLogStream` の不要なコールバックラッパー** - `handleClearLogs`
7. **`extractProgress` の条件チェック冗長性**

## Code Quality Issues (codex MCP)

### 高優先度
1. **ログコールバック例外によるパイプライン中断**
   - 場所: `executor.py:72`, `glossary_generator.py:105`, `glossary_refiner.py:105`
   - コールバックが例外をスローするとパイプラインが停止
   - 対策: try-except でコールバック呼び出しをガード

### 中優先度
2. **グローバルログ状態のプロジェクト衝突**
   - 場所: `logStore.ts:11`, `useLogStream.ts:41`
   - runId のみでキーイングしているため、異なるプロジェクトで同じ runId があると衝突
   - 対策: `(projectId, runId)` でキーイング

3. **Refiner での missing term 時の進捗スキップ**
   - 場所: `glossary_refiner.py:95`
   - term が見つからない場合、continue でコールバックがスキップされる
   - 対策: finally ブロックへの移動

### 低優先度
4. **`run_id` の型不整合**
   - バックエンド: None の可能性
   - フロントエンド: 必須
   - 対策: 型定義の統一

5. **`runId = 0` の falsy 問題**
   - 場所: `useLogStream.ts:46`
   - `if (!runId)` で 0 が "no run" 扱い
   - 対策: `runId === undefined` に変更

6. **`onComplete` の stale closure**
   - 場所: `useLogStream.ts:67`
   - 依存配列に含まれていない
   - 対策: 依存配列に追加

## 追加指摘

- **未使用パラメータ `conn`** - `_create_progress_callback` (将来のDB進捗更新用と思われるが未使用)

## Tasks

- [ ] 優先度に基づいて対応を決定
- [ ] テストを追加・更新
- [ ] 実装
- [ ] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [ ] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket.
- [ ] Code review by codex MCP. If the issue is not addressed immediately, create a ticket.
- [ ] Update docs/architecture/*.md
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## Notes

- 機能には影響しないリファクタリング
- 優先度低のため、他の作業に余裕がある時に対応
