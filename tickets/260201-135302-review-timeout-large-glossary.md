---
priority: 1
tags: [bug, backend, llm]
description: "GlossaryReviewerが大量の用語をレビューする際にタイムアウトで0件になる"
created_at: "2026-02-01T13:53:02Z"
started_at: 2026-02-01T13:55:32Z # Do not modify manually
closed_at: 2026-02-01T15:42:54Z # Do not modify manually
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

- [x] バッチ処理の設計・実装
- [x] タイムアウトエラーの明示的な報告
- [x] 既存テストの更新
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

- 発見経緯: Issues画面空問題の調査中に発見
- 影響: 用語数が多いプロジェクトではIssue検出が機能しない
- 暫定対応: 用語数を減らすか、手動でバッチ実行

---

## 設計（承認済み）

### 方針

バッチ処理を導入してタイムアウトを回避する。エラー時は例外を上位に伝播させ、ログ画面に表示する。

### 1. 基本アーキテクチャ

**変更対象**: `GlossaryReviewer.review()` メソッド

- 用語リストを20件ごとのバッチに分割
- 各バッチを順次LLMに送信してレビュー
- 全バッチの結果をマージして返却

```python
def review(self, glossary: Glossary, cancel_event: Event | None = None) -> list[GlossaryIssue] | None:
    if glossary.term_count == 0:
        return []

    all_terms = glossary.all_term_names
    batches = [all_terms[i:i+20] for i in range(0, len(all_terms), 20)]

    all_issues: list[GlossaryIssue] = []
    for batch_terms in batches:
        if cancel_event is not None and cancel_event.is_set():
            return None
        issues = self._review_batch(glossary, batch_terms)
        all_issues.extend(issues)

    return all_issues
```

### 2. バッチレビューの実装

**新規メソッド**: `_review_batch()` - 既存ロジックを抽出

- `_create_review_prompt()` を変更して用語リストを受け取るように
- **エラーハンドリング**: 例外をそのまま上位に伝播（graceful degradation削除）

### 3. エラーハンドリングとログ出力

**executor側** (`executor.py`):

```python
try:
    issues = reviewer.review(glossary, cancel_event=context.cancel_event)
except Exception as e:
    self._log(context, "error", f"Review failed: {e}")
    raise
```

**ログ出力例**:
- 成功時: `"Found 12 issues"` (info)
- 失敗時: `"Review failed: ReadTimeout"` (error)

### 4. バッチ進捗コールバック

**GlossaryReviewer.review()** に `batch_progress_callback` パラメータを追加:

```python
def review(
    self,
    glossary: Glossary,
    cancel_event: Event | None = None,
    batch_progress_callback: Callable[[int, int], None] | None = None,
) -> list[GlossaryIssue] | None:
```

**executor側**:

```python
def on_batch_progress(current: int, total: int) -> None:
    self._log(context, "info", f"Reviewing batch {current}/{total}...")

issues = reviewer.review(
    glossary,
    cancel_event=context.cancel_event,
    batch_progress_callback=on_batch_progress,
)
```

**ログ出力例** (97用語の場合):
```
Reviewing glossary...
Reviewing batch 1/5...
Reviewing batch 2/5...
Reviewing batch 3/5...
Reviewing batch 4/5...
Reviewing batch 5/5...
Found 12 issues
```

### 5. テスト方針

**新規テスト**:
1. **バッチ分割テスト**: 25用語 → 2バッチ(20+5)に分割されることを確認
2. **コールバックテスト**: `batch_progress_callback` が正しく呼ばれることを確認
3. **エラー伝播テスト**: LLMエラー時に例外が上位に伝播することを確認

**モック方針**: `llm_client.generate_structured()` をモックして複数回呼び出しを検証
