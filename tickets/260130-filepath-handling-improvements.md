---
priority: 4
tags: [improvement, backend, cross-platform]
description: "Document filepath handling: Additional improvements from code review"
created_at: "2026-01-30T22:50:00Z"
started_at: 2026-02-01T08:24:54Z
closed_at: 2026-02-01T08:45:12Z
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

- [x] 設計方針の決定（相対パス vs ファイル名のみ）
- [x] pathlib への統一
- [x] Posix スタイルセパレータへの統一
- [x] パス検証（`is_relative_to()` 使用）
- [x] API/スキーマドキュメントの更新
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

## Design (2026-02-01)

### 決定事項

1. **`file_name` カラム**: 相対パスを保存（例: `chapter1/intro.md`）
2. **セパレータ形式**: POSIX形式（`/`）に統一
3. **doc_root 外ファイル**: 拒否（`ValueError` を発生）
4. **API バリデーション**: `/` 許可、`..` と `\` を拒否

### ヘルパー関数

```python
def _safe_relative_path(file_path: Path, doc_root: Path) -> str:
    """ファイルパスを安全な相対パスに変換する。

    Args:
        file_path: 対象ファイルのパス
        doc_root: ドキュメントルート

    Returns:
        POSIX形式の相対パス

    Raises:
        ValueError: ファイルがdoc_root外の場合
    """
    resolved_file = file_path.resolve()
    resolved_root = doc_root.resolve()

    if not resolved_file.is_relative_to(resolved_root):
        raise ValueError(f"File is outside doc_root: {file_path}")

    return resolved_file.relative_to(resolved_root).as_posix()
```

### 変更ファイル

| ファイル | 変更内容 |
|----------|----------|
| `src/genglossary/runs/executor.py` | `os.path.relpath` → pathlib + `is_relative_to` 検証 |
| `src/genglossary/cli.py` | `rsplit` → pathlib + 相対パス変換 |
| `src/genglossary/api/routers/files.py` | `/` 許可、`..` と `\` を拒否 |
| `src/genglossary/api/schemas/file_schemas.py` | docstring 更新 |

### テストケース

1. **正常系**: `chapter1/intro.md` が正しく保存される
2. **パストラバーサル拒否**: `../secret.md` がエラー
3. **バックスラッシュ拒否**: `chapter1\intro.md` がエラー
4. **doc_root 外拒否**: `/etc/passwd` 相当がエラー
5. **POSIX形式確認**: Windows環境でも `/` で保存される

## Notes

- 260130-document-filepath-handling チケットから派生
- codex MCP レビューで指摘
- code-simplifier レビューで指摘
