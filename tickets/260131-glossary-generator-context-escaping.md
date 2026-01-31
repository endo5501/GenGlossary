---
priority: 1
tags: [security, improvement]
description: "GlossaryGenerator: Escape context XML tags to prevent prompt injection"
created_at: "2026-01-31T02:00:00Z"
started_at: 2026-01-31T01:39:56Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# GlossaryGenerator: Escape context XML tags to prevent prompt injection

## 概要

codex MCPのレビューにより、プロンプトインジェクション対策が不完全であることが発見された。

## 問題点

`_build_context_text` メソッドでコンテキストを `<context>` タグでラップしているが、ドキュメント内に `</context>` が含まれている場合、XMLタグが壊れてプロンプトが改変される可能性がある。

**現在のコード (src/genglossary/glossary_generator.py:274)**:
```python
def _build_context_text(self, occurrences: list[TermOccurrence]) -> str:
    if not occurrences:
        return "(ドキュメント内に出現箇所がありません)"

    lines = "\n".join(
        f"- {occ.context}"
        for occ in occurrences[: self.MAX_CONTEXT_COUNT]
    )
    return f"<context>\n{lines}\n</context>"
```

## 改善案

1. コンテキスト内の `</context>` や `<context>` をエスケープする
2. CDATAセクションを使用する
3. 別のエスケープ方式（Base64など）を検討

## Tasks

- [x] コンテキストエスケープロジックの設計
- [x] テストケースの作成（悪意のあるコンテキストを含むドキュメント）
- [x] 実装
- [x] 他のコードのコンテキストも確認し、同様の問題があるようであれば同様に対応する
  - 追加の脆弱性を発見 → 260131-prompt-injection-comprehensive-fix チケットで対応
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing

## 実装内容

- `_escape_context_tags()` ヘルパーメソッドを追加
- `<context>` → `&lt;context&gt;`、`</context>` → `&lt;/context&gt;` にエスケープ
- `_build_context_text()` でコンテキスト挿入前に自動エスケープ

## 関連

- 元チケット: 260130-glossary-generator-code-simplification
- codex MCPレビュー結果
- 後続チケット: 260131-prompt-injection-comprehensive-fix
