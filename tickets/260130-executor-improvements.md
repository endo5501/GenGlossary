---
priority: 3
tags: [improvement, backend, executor, code-quality]
description: "PipelineExecutor: Code quality improvements from review"
created_at: "2026-01-30T19:45:00Z"
started_at: 2026-01-30T11:19:46Z
closed_at: null
---

# PipelineExecutor: Code quality improvements from review

## 概要

code-simplifier agent と codex MCP のレビューで指摘されたコード品質改善を実施する。

## 改善項目

### 優先度高

#### 1. 型ヒントの明確化

**問題箇所**: `executor.py:314-318`
```python
extracted_terms: list | None = None  # 型が不明確
```

**提案**: `list[str] | list[ClassifiedTerm] | None` または Union 型で明確化。`type: ignore` コメントを削減。

#### 2. マジックストリングの定数化

**問題箇所**: スコープ名が文字列リテラルとして複数箇所で使用
```python
if scope == "full":  # マジックストリング
```

**提案**: `enum.Enum` または定数として定義
```python
class PipelineScope(Enum):
    FULL = "full"
    FROM_TERMS = "from_terms"
    PROVISIONAL_TO_REFINED = "provisional_to_refined"
```

#### 3. トランザクション安全性の追加

**問題箇所**: `executor.py:218-221`
```python
self._clear_tables_for_scope(conn, scope)  # クリア後に例外が発生すると不整合
```

**提案**: トランザクションでラップし、失敗時にロールバック

### 優先度中

#### 4. 進捗コールバックパターンの統一

**問題箇所**: `executor.py:348, 424`

**提案**: `_execute_with_progress()` ヘルパーメソッドで統一

#### 5. データベース読み込みロジックの統一

**問題箇所**: `executor.py:250-254, 328-331, 391-394`

**提案**: `_ensure_documents_loaded()` ヘルパーでキャンセルチェックとNullチェックを統一

#### 6. 用語集保存とログの統合

**提案**: `_save_glossary_terms()` に `log_action: str` パラメータを追加

### 優先度低

#### 7. 未使用パラメータの削除

**問題箇所**: `executor.py:160-175`
```python
conn: sqlite3.Connection,  # 使用されていない
```

**提案**: YAGNI 原則に従い削除

#### 8. 共通名詞フィルタリングの一貫性

**問題箇所**: Full run と resumed run で異なる動作

**提案**: スコープに関係なく一貫したフィルタリングを適用

### codex MCP レビュー追加指摘 (2026-01-30)

#### 9. file_name に完全パスを保存する問題 (Medium)

**問題箇所**: `executor.py:263-267`
```python
create_document(conn, document.file_path, ...)  # 完全パスが file_name に
```

**影響**: API/スキーマの期待（「パスなしのファイル名」）と矛盾。Files API やログを通じてサーバーパスが漏洩する可能性。

**提案**: 相対パス（`doc_root` からの相対）を使用するか、別の `file_path` カラムを追加

#### 10. 重複フィルタリングの適用範囲 (Low)

**問題箇所**: `executor.py:300-316, 350-355`

**影響**: 重複フィルタリングは DB 挿入にのみ適用され、用語集生成には未フィルタリングのリストが渡される。余分な LLM 呼び出しが発生する可能性。

**提案**: `generator.generate` に渡す前に重複を除去し、ユニーク数をログに記録

#### 11. issues が空の場合のキャンセルチェック (Low)

**問題箇所**: `executor.py:400-435`

**影響**: issues が空の場合、レビュー後のキャンセルチェックがない。キャンセル後も refined 出力が保存される可能性。

**提案**: refined 保存前にキャンセルチェックを追加

## 影響範囲

- `src/genglossary/runs/executor.py`

## Tasks

- [ ] 設計検討
- [ ] 型ヒントの明確化
- [ ] マジックストリングの定数化
- [ ] トランザクション安全性の追加
- [ ] 進捗コールバックパターンの統一
- [ ] データベース読み込みロジックの統一
- [ ] 未使用パラメータの削除
- [ ] 用語集保存とログの統合
- [ ] 共通名詞フィルタリングの一貫性
- [ ] file_name に完全パスを保存する問題
- [ ] 重複フィルタリングの適用範囲 
- [ ] issues が空の場合のキャンセルチェック
- [ ] Commit
- [ ] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [ ] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket.
- [ ] Code review by codex MCP. If the issue is not addressed immediately, create a ticket.
- [ ] Update docs/architecture/*.md
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## Notes

- 260130-executor-code-simplification チケットのレビューで発見
- code-simplifier agent および codex MCP レビューからの指摘
