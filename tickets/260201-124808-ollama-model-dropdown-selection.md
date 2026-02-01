---
priority: 3
tags: [ux, frontend, feature]
description: "Ollamaモデル選択時に接続先からモデル一覧を取得しドロップダウンで選択可能にする"
created_at: "2026-02-01T12:48:08Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# Ollamaモデルのドロップダウン選択

## 概要

Ollamaモデルを選択する際、接続先のOllamaサーバーから利用可能なモデル一覧を取得し、
ドロップダウンリストから選択できるようにする。

## 現状の問題

- モデル名を手動で入力する必要がある
- どのモデルが利用可能か確認するには、別途Ollamaの管理画面を確認する必要がある

## 期待する動作

1. Ollamaを選択した際、接続先URLに対してモデル一覧APIを呼び出す
2. 取得したモデル一覧をドロップダウンリストとして表示
3. ユーザーがリストからモデルを選択できる

## 技術詳細

- Ollama API: `GET /api/tags` でモデル一覧を取得可能
- レスポンス例: `{"models": [{"name": "llama2", ...}, ...]}`

## Tasks

- [ ] Ollamaモデル一覧取得APIの実装（バックエンド）
- [ ] フロントエンドにドロップダウンUIを実装
- [ ] API接続エラー時のフォールバック処理（手動入力に切り替え）
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

- Ollamaサーバーに接続できない場合は、従来通り手動入力を許可する
