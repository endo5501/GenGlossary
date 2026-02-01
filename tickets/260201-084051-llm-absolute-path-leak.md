---
priority: 3
tags: [security, backend]
description: "LLM prompts receive absolute file paths - potential privacy leak"
created_at: "2026-02-01T08:40:51Z"
started_at: 2026-02-01T08:45:57Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# LLM prompts receive absolute file paths (security/privacy leak)

## 概要

codex MCP のコードレビューで発見された問題。

`Document.file_path` は `DocumentLoader` から読み込んだ後も絶対パスのままで、LLMプロンプト（`glossary_generator`、`glossary_refiner` など）に渡される。DB保存時にはサニタイズされているが、LLM呼び出し時には絶対パスが漏洩している。

## 問題点

- サーバーのファイルパス構造が外部LLMサービスに送信される可能性
- ユーザー名やディレクトリ構造などのプライバシー情報が含まれる可能性
- "prevent server path leakage" の目標を達成できていない

## 影響箇所

- `src/genglossary/runs/executor.py:339-362`
- `src/genglossary/cli.py:169-188`
- `src/genglossary/glossary_generator.py`
- `src/genglossary/glossary_refiner.py`

## 推奨修正

`DocumentLoader` から読み込んだ直後、または LLM 呼び出し前に `Document.file_path` を相対パスに正規化する:

```python
# 例: documents リストを再構築
documents = [
    Document(
        file_path=to_safe_relative_path(doc.file_path, doc_root),
        content=doc.content
    )
    for doc in documents
]
```

## Tasks

- [ ] 問題の影響範囲を調査
- [ ] Document.file_path を正規化するタイミングを決定
- [ ] 実装
- [ ] テスト追加
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

- codex MCP レビューで指摘された High severity 問題
- 260130-filepath-handling-improvements から派生
