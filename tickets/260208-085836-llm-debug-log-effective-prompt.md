---
priority: 4
tags: [improvement, llm-debug]
description: "LLMデバッグロギングの総合改善（実効プロンプト記録、ファイル名衝突対策、エントリーポイント統一）"
created_at: "2026-02-08T08:58:36Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# LLMデバッグロギングの総合改善

## 概要

LLMデバッグロギングに関する3つの改善点を統合したチケット。

## 改善ポイント

### 1. 実効プロンプトの記録

`generate_structured` ラッパーは元の `prompt` 引数をログに記録するが、実際にLLMに送られるのは `_build_json_prompt()` で加工された `json_prompt` である。デバッグログが実際のリクエスト内容を正確に反映していない。

**修正案:**
- ラッパーで実効プロンプト（加工後のもの）をログに記録する
- または、具体的なクライアントのメソッド内でログ記録を行う

### 2. ファイル名衝突リスクとスレッドセーフティ

1. ファイル名は秒単位のタイムスタンプ + インスタンスごとのカウンター（1から開始）で構成される。同じ秒に新しいロガーインスタンスが作られると、既存ファイルが上書きされる可能性がある。
2. `self.counter` のインクリメントが同期されていない。並行呼び出しでレースコンディションが発生する可能性がある。

**修正案:**
- マイクロ秒やUUIDを使用する
- または排他的作成モード（`open(..., "x")`）でオープンして衝突時にリトライする
- `threading.Lock` でファイル名生成とインクリメントを保護する

### 3. 全エントリーポイントへの一貫適用

`RunManager` のパイプラインパスではデバッグロギングが接続されているが、他のLLMクライアント生成パス（CLI直接実行、APIルーターなど）ではデバッグオプションが渡されていない。`LLM_DEBUG` 環境変数を設定しても、一部のパスでしかログが生成されない。

**修正案:**
- `create_llm_client` 内で `Config().llm_debug` を直接参照するように集約する
- またはすべての呼び出し元で一貫してデバッグ引数を渡す

## Tasks

- [ ] 設計検討（3つの改善点の実装方針決定）
- [ ] テスト作成
- [ ] 実効プロンプト記録の実装
- [ ] ファイル名衝突対策・スレッドセーフティの実装
- [ ] エントリーポイント一貫適用の実装
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

- Codex MCPコードレビュー指摘事項 #3, #5, #6, #7
- 統合元チケット: 260208-085839-llm-debug-filename-collision-thread-safety, 260208-085841-llm-debug-consistent-entry-points
