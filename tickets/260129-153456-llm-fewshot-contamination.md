---
priority: 2
tags: [bug, llm, pipeline]
description: "GlossaryGenerator: Few-shot exampleがLLM出力に混入する"
created_at: "2026-01-29T15:34:56Z"
started_at: 2026-01-29T15:50:43Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# GlossaryGenerator: Few-shot exampleがLLM出力に混入する

## 概要

`glossary_generator.py`の定義生成プロンプトに含まれるFew-shot exampleが、LLMの実際の出力に混入している。

## 再現手順

1. GUIでプロジェクトを作成し、ドキュメントを登録
2. Runボタンを押してパイプラインを実行
3. Provisionalページで用語の定義を確認

## 現象

Provisional画面で、用語の定義が無関係な内容になっている：

```
Term: GenGlossaryプロジェクト
Definition: アソリウス島騎士団は、エデルト王国の辺境に位置するアソリウス島を守る戦闘組織...
```

「GenGlossaryプロジェクト」の定義に、全く無関係な「アソリウス島騎士団」の説明が入っている。

## 原因

`src/genglossary/glossary_generator.py:237-248` のプロンプトにFew-shot exampleとして「アソリウス島騎士団」の例が含まれており、LLMがこれをそのまま出力している：

```python
prompt = f"""用語: {term}
出現箇所とコンテキスト:
{context_text}

## Few-shot Examples

**用語:** アソリウス島騎士団
**定義:** エデルト王国の辺境、アソリウス島を守る騎士団。魔神討伐の最前線として重要な役割を担う。
**信頼度:** 0.9

文脈固有の意味を1-2文で説明。信頼度: 明確=0.8+, 推測可能=0.5-0.7, 不明確=0.0-0.4
JSON形式で回答してください: {{"definition": "...", "confidence": 0.0-1.0}}"""
```

## 期待される動作

- Few-shot exampleは参考として使用され、実際の出力には影響しない
- 各用語の定義は、ドキュメント内のコンテキストに基づいて生成される

## 提案する修正

1. プロンプト構造の改善
   - Few-shot exampleと実際のタスクを明確に区別
   - "Input:"/"Output:" 形式でexampleをラップ

2. Few-shot exampleの改善
   - 複数のexampleを使用して単一のexampleへの偏りを防ぐ
   - または、exampleを削除してzero-shotに変更

## 影響範囲

- `src/genglossary/glossary_generator.py`
- 同様の問題が `glossary_reviewer.py` にも存在する可能性

## Tasks

- [x] プロンプト構造を改善
- [x] テストで定義生成の品質を確認
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent
- [x] Code review by codex MCP
- [x] Update docs/architecture/*.md (不要: 内部実装の変更のみでAPIに影響なし)
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing


## Notes

- LLMのモデルやバージョンによって挙動が異なる可能性あり
- Ollamaローカル実行環境での検証が必要

## 実装結果

### 変更内容
- `src/genglossary/glossary_generator.py`: プロンプト構造を改善
  - 冒頭にシステム説明を追加
  - `## Example` セクションに例を配置し、「この例の内容をそのまま使わないでください」と明記
  - Input/Output形式で構造化
  - `## 今回の用語:` セクションで実際のタスクを明確に区別

### テスト
- `tests/test_glossary_generator.py`: プロンプト構造検証テストを2件追加
  - `test_definition_prompt_separates_example_from_task`
  - `test_definition_prompt_example_does_not_appear_in_task_section`

### 関連チケット
- `260129-155649-glossary-generator-prompt-refactoring`: code-simplifier/codex MCPからのリファクタリング提案をチケット化
