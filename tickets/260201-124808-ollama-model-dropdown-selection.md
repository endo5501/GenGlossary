---
priority: 3
tags: [ux, frontend, feature]
description: "Ollamaモデル選択時に接続先からモデル一覧を取得しドロップダウンで選択可能にする"
created_at: "2026-02-01T12:48:08Z"
started_at: 2026-02-02T13:33:30Z # Do not modify manually
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

- [x] Ollamaモデル一覧取得APIの実装（バックエンド）
- [x] フロントエンドにドロップダウンUIを実装
- [x] API接続エラー時のフォールバック処理（手動入力に切り替え）
- [x] Commit
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Update docs/architecture/*.md
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing


## Notes

- Ollamaサーバーに接続できない場合は、従来通り手動入力を許可する

---

## 設計（2026-02-02 承認済み）

### バックエンドAPI

**新規エンドポイント: `GET /api/ollama/models`**

| 項目 | 内容 |
|------|------|
| クエリパラメータ | `base_url` (optional, default: `http://localhost:11434`) |
| 成功レスポンス | `{"models": [{"name": "llama2"}, {"name": "llama3.2"}, ...]}` |
| エラーレスポンス | `{"detail": "Failed to connect to Ollama server"}` (503) |

**新規ファイル:**
- `src/genglossary/api/routers/ollama.py` - Ollamaルーター
- `src/genglossary/api/schemas/ollama_schemas.py` - スキーマ

**実装:** `OllamaClient` に `list_models()` メソッドを追加

### フロントエンド

**UI変更:**
1. Ollama選択時もベースURL入力欄を表示（デフォルト: `http://localhost:11434`）
2. モデル選択を `TextInput` → `Select`（ドロップダウン）に変更
3. 接続エラー時は `TextInput` にフォールバック + 警告メッセージ

**新規ファイル:**
- `frontend/src/api/hooks/useOllamaModels.ts` - モデル一覧取得フック（Debounce 500ms）

**対象コンポーネント:**
- SettingsPage
- CreateProject画面

### エラーハンドリング

| 状態 | UI表示 |
|------|--------|
| 取得中 | ドロップダウン無効化 + ローディング |
| 取得成功 | ドロップダウンでモデル選択 |
| 取得失敗 | TextInput + 警告「Ollamaサーバーに接続できません。モデル名を手動で入力してください」|

### 実装タスク（順序）

1. `OllamaClient.list_models()` メソッド追加（TDD）
2. `/api/ollama/models` エンドポイント作成（TDD）
3. `useOllamaModels` フック作成（TDD）
4. SettingsPage のUI変更
5. CreateProject のUI変更
6. 結合テスト・動作確認
