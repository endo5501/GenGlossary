---
priority: 4
tags: [refactoring, code-quality]
description: "GlossaryGenerator: プロンプト構築ロジックのリファクタリング"
created_at: "2026-01-29T15:56:49Z"
started_at: 2026-01-29T23:03:37Z # Do not modify manually
closed_at: 2026-01-30T09:16:17Z # Do not modify manually
---

# GlossaryGenerator: プロンプト構築ロジックのリファクタリング

## 概要

code-simplifier agentによるレビューに基づき、`glossary_generator.py`のコード品質を改善する。

## 改善対象

### 1. `_generate_definition`メソッド（優先度 高）

- **プロンプト構築ロジックの分離**: 長いf-stringを複数のヘルパーメソッドに分割
- **定数化**: マジックナンバー（`[:5]`）とFew-shot例をクラス定数として定義
- **メソッド分割案**:
  - `_build_context_text()`: コンテキストテキストの構築
  - `_build_definition_prompt()`: プロンプト全体の構築

### 2. `_contains_cjk`メソッド（優先度 中）

- 二重ループの簡潔化による可読性向上

### 3. `_filter_terms`メソッド（優先度 中）

- `type: ignore`コメントの削減と型安全性の向上

## 期待される効果

- テスト容易性の向上（プロンプト構築ロジックの単体テストが可能に）
- メンテナンス性の向上（Few-shot例の変更が容易に）
- 可読性の向上（メソッドの責務が明確に）

## Tasks

- [x] `_generate_definition`をヘルパーメソッドに分割
- [x] マジックナンバーとFew-shot例をクラス定数として定義
- [x] `_contains_cjk`の簡潔化
- [x] `_filter_terms`の型安全性向上
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket.
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket.
- [x] Update docs/architecture/*.md (内部リファクタリングのため更新不要)
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing


## 実施内容のサマリー

### 実装した変更

1. **プロンプト構築ロジックの分離**
   - `_build_context_text()`: コンテキストテキストの構築
   - `_build_definition_prompt()`: プロンプト全体の構築

2. **クラス定数の追加**
   - `MAX_CONTEXT_COUNT = 5`: マジックナンバーの定数化
   - `FEW_SHOT_EXAMPLE`: Few-shot例の定数化

3. **コード品質の改善**
   - `_is_cjk_char()`: CJK文字判定の抽出
   - `_filter_terms()`: `cast()`を使用して`type: ignore`を削除
   - 空白/空文字用語のフィルタリング追加（codexレビューの高優先度指摘）
   - `DefinitionResponse.confidence`: `confloat(ge=0, le=1)`で範囲制限

4. **プロンプトの改善**
   - `## End Example`デリミタを追加して例の終了を明示

### フォローアップチケット（作成済み）

- `260130-glossary-generator-error-handling.md`: print()をloggingに置き換え
- `260130-glossary-generator-prompt-security.md`: プロンプトインジェクション対策

## Notes

- 既存のテストに影響を与えないよう、段階的に適用する
- 関連チケット: 260129-153456-llm-fewshot-contamination（Few-shot混入問題の修正）

## codex MCPからの追加提案

- 例で具体的な用語（「アソリウス島騎士団」）の代わりにプレースホルダー（`<TERM>`, `<CONTEXT>`）を使用
- 「## End Example」デリミタを追加して例の終了を明示
- 例の入力ラベル（「出現箇所」）と実際のタスクラベル（「出現箇所とコンテキスト」）を統一
- LLM clientがsystem roleをサポートしていれば、システム指示をsystem roleで送信
