---
priority: 1
tags: [improvement, refactoring, code-quality]
description: "GlossaryGenerator: コード簡素化とリファクタリング"
created_at: "2026-01-30T10:00:00Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# GlossaryGenerator: コード簡素化とリファクタリング

## 概要

code-simplifier agentのレビューにより、`glossary_generator.py`の複数の改善点が特定された。

## 改善点一覧

### 高優先度

#### 1. 重複した進捗コールバック処理の抽出（行124-135）

**問題点**:
```python
if progress_callback is not None:
    try:
        progress_callback(idx, total_terms)
    except Exception:
        pass
if term_progress_callback is not None:
    try:
        term_progress_callback(idx, total_terms, term_name)
    except Exception:
        pass
```

- 2つのコールバックで同じtry-exceptパターンが繰り返されている
- DRY原則違反

**改善案**: ヘルパーメソッドに抽出

#### 2. 型判定ロジックの簡素化（行155-172）

**問題点**:
```python
if isinstance(terms[0], str):
    str_terms = cast(list[str], terms)
    return [t for t in str_terms if t.strip()]

classified_terms = cast(list[ClassifiedTerm], terms)
```

- `terms[0]`を使った型判定
- 同じフィルタリングロジック（`strip()`チェック）が2箇所で繰り返し

**改善案**:
- `_filter_terms`で統一された型を返す
- または、型ごとに別のプライベートメソッドを作成

### 中優先度

#### 3. CJK関連ロジックの分離

**問題点**:
- `CJK_RANGES`, `_is_cjk_char`, `_contains_cjk` が `GlossaryGenerator` に含まれている
- 他のクラスでも再利用可能な汎用ロジック

**改善案**: ユーティリティモジュールに抽出

#### 4. プロンプトテンプレートの外部化（行278-306）

**問題点**:
- 長い複数行文字列がメソッド内にハードコード
- 変更・テストが困難

**改善案**:
- プロンプトをクラス定数として定義
- または、外部ファイル/テンプレートエンジンで管理

### 低優先度

#### 5. マジックナンバーの定数化

**問題点**:
- `context_lines=1` がハードコード（行206）

**改善案**: クラス定数 `DEFAULT_CONTEXT_LINES = 1` を定義

#### 6. 例外処理の具体化

**問題点**:
- `except Exception` で全ての例外をキャッチ

**改善案**: `BaseLLMClient` が投げる具体的な例外型をキャッチ

## Tasks

- [ ] 重複した進捗コールバック処理をヘルパーメソッドに抽出
- [ ] 型判定ロジックの簡素化を検討・実装
- [ ] CJK関連ロジックをユーティリティに抽出（オプション）
- [ ] マジックナンバーの定数化
- [ ] 例外処理の具体化
- [ ] Run static analysis (`pyright`) before reviewing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before reviewing and pass all tests (No exceptions)
- [ ] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket.
- [ ] Code review by codex MCP. If the issue is not addressed immediately, create a ticket.
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## 関連

- 元チケット: 260130-glossary-generator-error-handling
- code-simplifier agentレビュー結果
