---
priority: 3
tags: [improvement, backend, executor, code-quality]
description: "PipelineExecutor: Code quality improvements from review"
created_at: "2026-01-30T19:45:00Z"
started_at: null
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
