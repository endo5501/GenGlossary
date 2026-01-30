---
priority: 8
tags: [feature, backend]
description: "DB progress update implementation decision"
created_at: "2026-01-30T09:45:00Z"
started_at: null
closed_at: null
---

# DB progress update implementation decision

## 概要

`_create_progress_callback` の `conn` パラメータが未使用。
DB進捗更新を実装するか、パラメータを削除するかを判断して対応する。

## 背景

- `runs` テーブルには `progress_current`, `progress_total`, `current_step` カラムが存在
- `update_run_progress` 関数も `runs_repository.py` に実装済み
- しかし `_create_progress_callback` で `conn` を受け取りながら使用していない
- UIがポーリングに依存している場合、進捗が更新されない問題がある

## 選択肢

### A) DB進捗更新を実装
- `_create_progress_callback` 内で `update_run_progress` を呼び出す
- メリット: `/runs/{id}` ポーリングで進捗を取得できる
- デメリット: DB書き込みオーバーヘッド

### B) パラメータを削除
- `conn` パラメータを削除し、進捗はSSEログのみで提供
- メリット: シンプル、現状の動作を明確化
- デメリット: ポーリング依存のクライアントは進捗を取得できない

## 調査事項

- [ ] UIがポーリングを使用しているか、SSEのみかを確認
- [ ] どちらの方式が適切か判断

## Tasks

- [ ] 調査と判断
- [ ] テストを追加・更新
- [ ] 実装
- [ ] Run static analysis and pass all tests
- [ ] Run tests and pass all tests
- [ ] Get developer approval before closing
