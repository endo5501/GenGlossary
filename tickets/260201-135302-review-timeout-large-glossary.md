---
priority: 1
tags: [bug, backend, llm]
description: "GlossaryReviewerが大量の用語をレビューする際にタイムアウトで0件になる"
created_at: "2026-02-01T13:53:02Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# GlossaryReviewer タイムアウト問題

## 概要

大量の用語（50件以上）をGlossaryReviewerでレビューする際、LLMリクエストがタイムアウトし、例外がキャッチされて0件のissueが返される。ユーザーには「Found 0 issues」と表示されるが、実際にはレビューが失敗している。

## 現象

| 用語数 | 結果 |
|--------|------|
| 5件 | 4 issues 検出 ✅ |
| 10件 | 6 issues 検出 ✅ |
| 20件 | 7 issues 検出 ✅ |
| 50件 | タイムアウト → 0 issues ❌ |
| 97件 | タイムアウト → 0 issues ❌ |

## 根本原因

1. `GlossaryReviewer.review()`でLLMリクエストがタイムアウト（180秒）
2. 例外が`except Exception`でキャッチされ、空のリストが返される（graceful degradation）
3. executorは「Found 0 issues」とログ出力し、処理を続行
4. ユーザーはレビューが失敗したことを認識できない

## 関連コード

- `src/genglossary/glossary_reviewer.py:70-77` - 例外キャッチで空リスト返却
- `src/genglossary/llm/ollama_client.py:119` - 180秒タイムアウト
- `src/genglossary/runs/executor.py:535` - "Found N issues" ログ出力

## 解決策の候補

1. **バッチ処理**: 用語をバッチに分けてレビュー（推奨）
2. **タイムアウト延長**: より長いタイムアウト設定（根本解決ではない）
3. **エラー報告改善**: タイムアウト時にユーザーに明示的に報告

## Tasks

- [ ] バッチ処理の設計・実装
- [ ] タイムアウトエラーの明示的な報告
- [ ] 既存テストの更新
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

- 発見経緯: Issues画面空問題の調査中に発見
- 影響: 用語数が多いプロジェクトではIssue検出が機能しない
- 暫定対応: 用語数を減らすか、手動でバッチ実行
