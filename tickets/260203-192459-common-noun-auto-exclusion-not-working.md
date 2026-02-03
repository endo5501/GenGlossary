---
priority: 2
tags: [bug, excluded-terms]
description: "common_noun自動除外が動作していない"
created_at: "2026-02-03T19:24:59Z"
started_at: 2026-02-03T19:27:51Z # Do not modify manually
closed_at: 2026-02-03T19:38:15Z # Do not modify manually
---

# common_noun自動除外が動作していない

## 概要

本来の仕様では、LLMによる用語分類で`common_noun`（一般名詞）に分類された用語は、除外用語リストに自動で登録されるべきです。しかし、現在この仕組みが動作していません。

## 期待される動作

1. 用語抽出ステップでLLMが用語を6カテゴリに分類
2. `common_noun`に分類された用語は自動的に除外用語テーブル（`terms_excluded`）に追加される
3. 次回以降の用語抽出で、これらの用語は候補から除外される

## 現在の動作

`common_noun`に分類された用語が除外用語テーブルに登録されていない。

## 関連コード

- `src/genglossary/term_extractor.py`: `_add_common_nouns_to_exclusion` メソッド
- API経由での実行時に`excluded_term_repo`が渡されていない可能性

## Tasks

- [x] 問題の原因を調査（API経由での実行フローを確認）
- [x] `RunManager`または関連コードで`excluded_term_repo`が正しく渡されているか確認
- [x] 修正の実装
- [x] テストの追加
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

- 仕様は `.claude/rules/00-overview.md` のステップ1で定義
- `source`フィールドは`"auto"`を使用
