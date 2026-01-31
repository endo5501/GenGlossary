---
priority: 1
tags: [security, improvement]
description: "GlossaryGenerator: Escape context XML tags to prevent prompt injection"
created_at: "2026-01-31T02:00:00Z"
started_at: null  # Do not modify manually
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

- [ ] コンテキストエスケープロジックの設計
- [ ] テストケースの作成（悪意のあるコンテキストを含むドキュメント）
- [ ] 実装
- [ ] 他のコードのコンテキストも確認し、同様の問題があるようであれば同様に対応すする
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## 関連

- 元チケット: 260130-glossary-generator-code-simplification
- codex MCPレビュー結果
