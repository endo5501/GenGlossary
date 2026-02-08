---
priority: 2
tags: [feature, backend, debug]
description: "Add LLM debug mode to log prompts and responses for troubleshooting"
created_at: "2026-02-07T16:09:22Z"
started_at: 2026-02-08T08:20:48Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# LLMデバッグログ機能の追加

## 概要

現在、LLMに送信しているプロンプトや受信したレスポンスの内容を確認する手段がない。適切なプロンプトが送受信されているかを検証するためのデバッグ機能を追加する。

## ユースケース

- プロンプトの内容が意図通りか確認したい
- LLMからのレスポンスが期待通りか確認したい
- 用語集生成の品質問題を調査したい
- 同義語情報やuser_notesがプロンプトに正しく含まれているか確認したい

## 設計

### 有効化方法

- `Config` に `LLM_DEBUG: bool = False` フィールドを追加
- 環境変数 `LLM_DEBUG=true` または CLI `--llm-debug` フラグで有効化
- デフォルトOFF

### 変更対象コンポーネント

1. **`Config`** — `LLM_DEBUG` フィールド追加
2. **`BaseLLMClient`** — デバッグログ出力ロジックを基底クラスに追加
3. **`create_llm_client()` ファクトリ** — `llm_debug` と `debug_dir` をクライアントに渡す
4. **`cli_api.py`** — `--llm-debug` オプション追加
5. **`.gitignore`** — `llm-debug/` を追加

### データフロー

```
CLI --llm-debug → Config.llm_debug=True
    → create_llm_client(config) → BaseLLMClient(debug_dir=...)
        → generate() / generate_structured()
            → _write_debug_log(request)
            → (LLM呼び出し)
            → _write_debug_log(response)
```

### 出力先

- `{db_path の親ディレクトリ}/llm-debug/`
- CLI直接実行時は `./llm-debug/`（db_pathが未指定の場合）
- ディレクトリは初回書き込み時に自動作成

### ファイル形式

ファイル名: `{YYYYMMDD}-{HHmmss}-{連番4桁}.txt`

```
llm-debug/
  20260208-103000-0001.txt
  20260208-103005-0002.txt
  20260208-110030-0001.txt   # 別のラン → 連番リセット
```

ファイル内容（リクエストとレスポンスを1ファイルに統合）:

```
# Timestamp: 2026-02-08T10:30:00
# Model: dengcao/Qwen3-30B-A3B-Instruct-2507
# Method: generate_structured
# Duration: 3.2s

## REQUEST
(プロンプト本文)

## RESPONSE
(レスポンス本文)
```

連番はラン（パイプライン実行）開始時にリセットし、同一ラン内での呼び出し順序を示す。

## Tasks

- [x] 設計検討（出力形式、出力先、有効化方法）
- [ ] Config に LLM_DEBUG フィールドを追加
- [ ] BaseLLMClient にデバッグログ出力ロジックを追加
- [ ] create_llm_client() ファクトリにデバッグ設定を渡す
- [ ] CLI に --llm-debug オプションを追加
- [ ] .gitignore に llm-debug/ を追加
- [ ] Commit
- [ ] Run static analysis (`pyright`) before reviewing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before reviewing and pass all tests (No exceptions)
- [ ] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Update docs (glob: "*.md" in ./docs/architecture)
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## Notes

- 本番運用では無効にすべき（デフォルトOFF）
- ログファイルにはセンシティブな情報が含まれる可能性があるため、.gitignoreに追加推奨
- 将来的にはWeb UIからもデバッグログを閲覧できるようにすることも検討可能
