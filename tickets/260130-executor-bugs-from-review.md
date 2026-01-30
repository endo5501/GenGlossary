---
priority: 2
tags: [bugfix, backend, executor]
description: "PipelineExecutor: Bug fixes from code review"
created_at: "2026-01-30T19:45:00Z"
started_at: null
closed_at: null
---

# PipelineExecutor: Bug fixes from code review

## 概要

code-simplifier agent と codex MCP のレビューで発見された PipelineExecutor のバグを修正する。

## 問題の詳細

### A. Refined glossary が issues なし時に保存されない (High)

**問題箇所**: `executor.py:415` 付近
```python
if not issues:
    return  # ← ここで終了し、refined glossary が保存されない
```

**影響**: CLI では issues がなくても refined を保存するが、GUI/DB 実行では空になる。下流で refined データを使う際に問題が発生する。

### B. 重複用語挿入でパイプラインがクラッシュ (High)

**問題箇所**: `executor.py:301-307`
```python
for classified_term in extracted_terms:
    create_term(conn, classified_term.term, ...)  # UNIQUE制約違反で IntegrityError
```

**影響**: LLM が同じ用語を複数回抽出した場合、`sqlite3.IntegrityError` が発生しパイプラインが中断。部分的な状態が残る。

### C. ドキュメントファイル名衝突で挿入失敗 (Medium)

**問題箇所**: `executor.py:265-268`
```python
file_name = Path(document.file_path).name  # basename のみ
create_document(conn, file_name, ...)  # file_name は UNIQUE
```

**影響**: 異なるフォルダにある同名ファイル（例: `docs/README.md` と `examples/README.md`）を読み込むと `IntegrityError` が発生。

## 対策案

1. **A**: issues がなくても provisional glossary を refined としてコピーする
2. **B**: 重複チェックまたは `INSERT OR IGNORE` を使用
3. **C**: ファイル名に相対パスを含めるか、衝突時にサフィックスを追加

## 影響範囲

- `src/genglossary/runs/executor.py`
- `src/genglossary/db/term_repository.py` (B の場合)
- `src/genglossary/db/document_repository.py` (C の場合)

## Tasks

- [ ] テストを書いて問題を再現
- [ ] 修正実装
- [ ] Run static analysis (`pyright`)
- [ ] Run tests (`uv run pytest`)
- [ ] Get developer approval

## Notes

- 260130-executor-code-simplification チケットのレビューで発見
- codex MCP レビューからの指摘
