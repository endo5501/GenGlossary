---
priority: 4
tags: [security, improvement]
description: "GlossaryGenerator: プロンプトインジェクション対策"
created_at: "2026-01-30T08:21:00Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# GlossaryGenerator: プロンプトインジェクション対策

## 概要

codex MCPレビューにより、プロンプトインジェクションリスクが指摘された。

## 現状の問題

- コンテキスト行がそのままプロンプトに挿入される
- ドキュメント内に "Output:" や指示文が含まれると、LLMの応答を乗っ取られる可能性

## 改善案

- コンテキストをフェンスブロックまたはXMLタグで囲む
- モデルにコンテキストを「データ」として扱うよう明示的に指示

例:
```python
context_text = f"""<context>
{contexts_joined}
</context>"""
```

## Tasks

- [ ] プロンプトの安全性を向上
- [ ] テスト追加（悪意のあるコンテキストを含むケース）

## 関連

- 元チケット: 260129-155649-glossary-generator-prompt-refactoring
