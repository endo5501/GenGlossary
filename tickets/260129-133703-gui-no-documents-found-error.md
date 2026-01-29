---
priority: 1
tags: [bug, gui]
description: "GUI: Run実行時に「No documents found」エラーが発生する問題"
created_at: "2026-01-29T13:37:03Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# GUI: Run実行時に「No documents found」エラーが発生する問題

## 概要

GUI機能でOllama利用のプロジェクトを作成し、テキストファイルを登録してRunボタンを押したところ、以下のエラーが発生して処理が停止する。STOPボタンを押しても反応がない。

### 再現手順

1. GUIでOllama利用のプロジェクトを作成
2. テキストファイルを1つ登録
3. 全体実行のRunボタンを押す

### 発生するエラーログ

```
[INFO] Starting pipeline execution: full
[INFO] Loading documents...
[ERROR] No documents found
[ERROR] Run failed: No documents found in doc_root
```

### 期待される動作

- 登録したテキストファイルが正しく読み込まれ、用語抽出処理が開始される
- STOPボタンが押されたら処理が中断される

## 調査ポイント

1. **ドキュメント登録の永続化**: GUIで登録したファイルが正しく保存されているか
2. **doc_rootパスの問題**: プロジェクト設定のdoc_rootが正しく設定・参照されているか
3. **DocumentLoaderの挙動**: ドキュメント読み込み時のパス解決が正しいか
4. **STOPボタンの問題**: 処理中断機能が正しく動作しているか

## Tasks

- [ ] 問題の原因を特定する
- [ ] 修正を実装する
- [ ] 修正が正しく動作することを確認する
- [ ] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [ ] Code simplification review using code-simplifier agent
- [ ] Code review by codex MCP
- [ ] Update docs/architecture/*.md
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing


## Notes

- 関連コード: `gui/src/`, `src/genglossary/`
- 既存の類似修正: c364d0b (Fix GUI bugs: document persistence, Run execution, and cache invalidation)
