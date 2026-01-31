---
priority: 4
tags: [improvement, backend, cross-platform]
description: "Document filepath handling: Additional improvements from code review"
created_at: "2026-01-30T22:50:00Z"
started_at: null
closed_at: null
---

# Document filepath handling: Additional improvements

## 概要

260130-document-filepath-handling チケットの実装後、code-simplifier と codex MCP のレビューで指摘された追加の改善点。

## 指摘された問題

### Medium 優先度

1. **Windows ドライブ間パス問題**
   - `os.path.relpath()` は Windows で異なるドライブ間のパスに対して `ValueError` を発生させる
   - 対策: `Path.resolve()` + `is_relative_to()` でガード

2. **API/CLI との一貫性**
   - CLI: `file_name` に相対パス（`chapter1/intro.md`）を保存
   - GUI: `file_name` にファイル名のみ（`intro.md`）を保存
   - `_validate_file_name` は `/` を拒否
   - スキーマドキュメントには "without path" と記載
   - 対策: どちらかに統一し、ドキュメントを更新

### Low 優先度

3. **`../..` セグメントの可能性**
   - `relpath` は `doc_root` 外のファイルに対して `../..` を生成
   - セキュリティ/ポータビリティの意図に反する
   - 対策: `is_relative_to()` で検証し、外部ファイルを拒否

4. **OS 固有セパレータ**
   - Windows は `\\`、Unix は `/` を使用
   - DB が異なる OS 間で移動した場合に不整合
   - 対策: `Path(...).as_posix()` で統一

5. **pathlib への統一** (code-simplifier)
   - プロジェクト全体が `pathlib.Path` を使用
   - `os.path.relpath()` を `Path.relative_to()` に変更
   - 注意: `relative_to()` は基準外パスで `ValueError` を投げる

## 影響範囲

- `src/genglossary/runs/executor.py`
- `src/genglossary/api/routers/files.py`
- `src/genglossary/api/schemas/file_schemas.py`
- `src/genglossary/cli.py`

## Tasks

- [ ] 設計方針の決定（相対パス vs ファイル名のみ）
- [ ] pathlib への統一
- [ ] Posix スタイルセパレータへの統一
- [ ] パス検証（`is_relative_to()` 使用）
- [ ] API/スキーマドキュメントの更新
- [ ] テストの追加
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

- 260130-document-filepath-handling チケットから派生
- codex MCP レビューで指摘
- code-simplifier レビューで指摘
