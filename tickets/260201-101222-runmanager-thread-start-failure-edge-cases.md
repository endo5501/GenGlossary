---
priority: 6
tags: [improvement, backend, threading]
description: "RunManager: Handle thread start failure edge cases"
created_at: "2026-02-01T10:12:22Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# RunManager: Handle thread start failure edge cases

## 概要

`start_run()` のスレッド起動失敗時のエッジケース処理を改善する。codex MCP レビューで指摘された問題点を対処する。

## 現状の問題

### codex MCP レビューからの指摘

**場所**: `src/genglossary/runs/manager.py` (start_run, lines 71-104)

1. **例外マスキング**: except ブロック内で `update_run_status` がスローすると、元の例外（スレッド起動失敗）が置き換えられる可能性がある

2. **`finished_at` 未設定**: スレッド起動失敗時に `finished_at` が設定されないため、失敗した run にタイムスタンプがない

3. **完了シグナル・subscriber クリーンアップなし**: スレッド起動失敗時に、登録済みの subscriber に完了シグナルが送信されず、クリーンアップも行われない

4. **`self._thread` が未開始状態で残る**: `Thread.start()` 失敗時に、`_thread` が未開始のスレッドを指したまま

## 提案する解決策

1. DB 更新を try/except でラップし、元の例外をマスクしないようにする
2. 失敗時に `finished_at` を設定する
3. 失敗時に完了シグナルを送信し、subscriber をクリーンアップする
4. 失敗時に `self._thread = None` をセットする

## Tasks

- [ ] 設計レビュー・承認
- [ ] 実装
- [ ] テストの更新
- [ ] Commit
- [ ] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [ ] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Update docs/architecture/*.md
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## Notes

- 260131-134730-runmanager-start-run-state-consistency チケットの codex MCP レビューで指摘
- 現状は重大な問題ではないが、堅牢性向上のために対処が望ましい
