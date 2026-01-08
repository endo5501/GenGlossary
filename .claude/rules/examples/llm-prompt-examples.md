# LLMプロンプト例集

このドキュメントでは、GenGlossaryの4ステップそれぞれで使用するプロンプトの例を示します。

## プロンプト設計の原則

### ✅ 良いプロンプトの特徴

1. **タスクを明確に定義**: 何をすべきか具体的に記述
2. **基準を示す**: 抽出・生成の基準を明示
3. **出力形式を指定**: JSON schema を含める
4. **例を提供**: Few-shot examples で理解を助ける
5. **制約を明記**: 何を含めて、何を除外するか

### ❌ 悪いプロンプトの特徴

- 曖昧な指示（"用語を抽出してください"のみ）
- 出力形式が不明確
- 基準がない
- 例がない

## ステップ1: 用語抽出

### ✅ 良いプロンプト例

```python
TERM_EXTRACTION_PROMPT = """
以下の文章から専門用語を抽出してください。

# 抽出基準
- 文章内で2回以上出現する名詞
- 固有名詞、専門用語、技術用語を優先
- 一般的な単語（「これ」「それ」「もの」など）は除外
- 複合語も1つの用語として扱う（例: 「量子コンピュータ」）

# 入力文章
{document_content}

# 出力形式
JSON形式で以下の構造で返してください:
{{
  "terms": ["用語1", "用語2", "用語3"]
}}

# 例
入力: "量子コンピュータは量子ビットを使用します。量子ビットは重ね合わせという性質を持ちます。"
出力: {{"terms": ["量子コンピュータ", "量子ビット", "重ね合わせ"]}}
"""
```

**ポイント**:
- ✅ 抽出基準が具体的（2回以上、固有名詞優先、除外ルール）
- ✅ JSON schema を明示
- ✅ Few-shot example を提供

### ❌ 悪いプロンプト例

```python
# 曖昧で基準がない
prompt = "文章から用語を抽出してください。"

# 出力形式が不明確
prompt = "文章から重要な単語をリストで返してください。"
```

## ステップ2: 用語集生成

### ✅ 良いプロンプト例

```python
GLOSSARY_GENERATION_PROMPT = """
以下の用語について、文章内での意味を定義してください。

# 用語
{term}

# 文章
{document_content}

# 定義作成の基準
- 文章内での使われ方に基づいて定義する
- 一般的な辞書の定義ではなく、この文章での意味を説明
- 2-3文程度で簡潔に
- 出現箇所（行番号）を明記
- 関連する用語があれば列挙

# 出力形式
JSON形式で以下の構造で返してください:
{{
  "term": "用語名",
  "definition": "この文章内での定義",
  "occurrences": [
    {{"line_number": 1, "context": "用語が使われている文"}},
    {{"line_number": 5, "context": "用語が使われている文"}}
  ],
  "related_terms": ["関連用語1", "関連用語2"],
  "confidence": 0.9
}}

# 例
用語: "量子ビット"
出力:
{{
  "term": "量子ビット",
  "definition": "量子コンピュータで情報を扱う基本単位。0と1の状態を同時に保持できる重ね合わせという性質を持つ。",
  "occurrences": [
    {{"line_number": 3, "context": "量子コンピュータは量子ビット（キュービット）を使用します。"}},
    {{"line_number": 4, "context": "キュービットは0と1の状態を同時に保持する重ね合わせという性質を持ちます。"}}
  ],
  "related_terms": ["量子コンピュータ", "キュービット", "重ね合わせ"],
  "confidence": 0.95
}}
"""
```

**ポイント**:
- ✅ 定義作成の基準が明確
- ✅ 出現箇所、関連用語、信頼度を含む
- ✅ Few-shot example で期待する形式を示す

### ❌ 悪いプロンプト例

```python
# 基準がない
prompt = f"'{term}' を定義してください。"

# 出力形式が不明確
prompt = f"'{term}' の意味を説明してください。文章: {content}"
```

## ステップ3: 精査

### ✅ 良いプロンプト例

```python
GLOSSARY_REVIEW_PROMPT = """
以下の用語集を精査し、不明な点や矛盾している点を列挙してください。

# 用語集
{glossary_json}

# 精査基準
1. **不明確な定義**: 曖昧で具体性に欠ける定義
2. **矛盾**: 用語間で矛盾する説明
3. **不足**: 重要な情報が欠けている
4. **重複**: 同じ意味の用語が複数存在
5. **誤り**: 明らかに誤った説明

# 出力形式
JSON形式で以下の構造で返してください:
{{
  "issues": [
    {{
      "term": "問題がある用語",
      "issue_type": "unclear | contradiction | missing | duplicate | error",
      "description": "具体的な問題の説明",
      "suggestion": "改善案（あれば）"
    }}
  ]
}}

# 例
入力:
{{
  "terms": [
    {{"term": "量子ビット", "definition": "量子の単位"}},
    {{"term": "キュービット", "definition": "量子コンピュータで情報を扱う基本単位"}}
  ]
}}

出力:
{{
  "issues": [
    {{
      "term": "量子ビット",
      "issue_type": "unclear",
      "description": "定義が曖昧で具体性に欠ける。「量子の単位」では何の単位か不明。",
      "suggestion": "「量子コンピュータで情報を扱う基本単位」のように具体的に説明する"
    }},
    {{
      "term": "量子ビット / キュービット",
      "issue_type": "duplicate",
      "description": "量子ビットとキュービットは同じ意味だが、別の用語として定義されている。",
      "suggestion": "1つの用語にまとめ、別名として明記する"
    }}
  ]
}}
"""
```

**ポイント**:
- ✅ 精査基準が5つのカテゴリに分類
- ✅ 問題タイプを明確に指定
- ✅ 改善案も含める
- ✅ Few-shot example で問題の見つけ方を示す

## ステップ4: 改善

### ✅ 良いプロンプト例

```python
GLOSSARY_REFINE_PROMPT = """
以下の用語の定義を、指摘された問題に基づいて改善してください。

# 元の用語
{term_json}

# 指摘された問題
{issue_json}

# 参照する文章
{document_content}

# 改善基準
- 指摘された問題を解決する
- 文章内の情報に基づいて正確に定義する
- 具体的で明確な説明にする
- 関連用語との関係を明記する
- 矛盾がないようにする

# 出力形式
JSON形式で以下の構造で返してください:
{{
  "term": "用語名",
  "definition": "改善された定義",
  "occurrences": [{{"line_number": 1, "context": "..."}}],
  "related_terms": ["関連用語"],
  "improvements": ["どのように改善したか"],
  "confidence": 0.95
}}

# 例
元の用語:
{{"term": "量子ビット", "definition": "量子の単位"}}

指摘された問題:
{{"issue_type": "unclear", "description": "定義が曖昧"}}

出力:
{{
  "term": "量子ビット",
  "definition": "量子コンピュータで情報を扱う基本単位。従来のビット（0または1）と異なり、0と1の状態を同時に保持する重ね合わせという性質を持つ。キュービットとも呼ばれる。",
  "occurrences": [
    {{"line_number": 3, "context": "量子コンピュータは量子ビット（キュービット）を使用します。"}}
  ],
  "related_terms": ["量子コンピュータ", "キュービット", "重ね合わせ", "ビット"],
  "improvements": [
    "「量子の単位」という曖昧な表現を、具体的な機能の説明に変更",
    "従来のビットとの違いを明記",
    "キュービットという別名を追加"
  ],
  "confidence": 0.95
}}
"""
```

**ポイント**:
- ✅ 元の用語、問題、文章の3つを提供
- ✅ 改善基準を明確に
- ✅ 改善内容を `improvements` フィールドで説明
- ✅ Few-shot example で改善の方法を示す

## プロンプトテンプレートの管理

### ファイル構成

```
src/genglossary/
└── prompts/
    ├── __init__.py
    ├── term_extraction.py
    ├── glossary_generation.py
    ├── glossary_review.py
    └── glossary_refine.py
```

### テンプレートクラスの例

```python
# src/genglossary/prompts/term_extraction.py

from typing import Protocol

class TermExtractionPrompt(Protocol):
    """用語抽出プロンプトのインターフェース."""

    @staticmethod
    def build(document_content: str) -> str:
        """プロンプトを構築."""
        return f"""
以下の文章から専門用語を抽出してください。

# 抽出基準
- 文章内で2回以上出現する名詞
- 固有名詞、専門用語を優先
- 一般的な単語は除外

# 入力文章
{document_content}

# 出力形式
JSON形式: {{"terms": ["用語1", "用語2"]}}
"""
```

### 使用例

```python
class TermExtractor:
    def extract(self, document: Document) -> list[str]:
        """用語を抽出."""
        prompt = TermExtractionPrompt.build(document.content)
        response = self.llm_client.generate(prompt)
        return self._parse_response(response)
```

## Few-shot Examples の活用

### パターン1: シンプルな例

```python
prompt = f"""
文章から用語を抽出してください。

# 例
入力: "AIは人工知能の略です。"
出力: {{"terms": ["AI", "人工知能"]}}

# 入力
{document_content}

# 出力（JSON形式）
"""
```

### パターン2: 複数の例

```python
prompt = f"""
文章から用語を抽出してください。

# 例1
入力: "AIは人工知能の略です。"
出力: {{"terms": ["AI", "人工知能"]}}

# 例2
入力: "量子コンピュータは量子ビットを使用します。"
出力: {{"terms": ["量子コンピュータ", "量子ビット"]}}

# 例3
入力: "これはペンです。それは本です。"
出力: {{"terms": ["ペン", "本"]}}

# 入力
{document_content}
"""
```

## プロンプトのバージョン管理

```python
# バージョン管理の例
class PromptVersion:
    V1 = "v1"  # 初期バージョン
    V2 = "v2"  # Few-shot examples 追加
    V3 = "v3"  # 出力形式を改善

class TermExtractionPrompt:
    @staticmethod
    def build(document_content: str, version: str = PromptVersion.V3) -> str:
        if version == PromptVersion.V1:
            return _build_v1(document_content)
        elif version == PromptVersion.V2:
            return _build_v2(document_content)
        else:
            return _build_v3(document_content)
```

## 関連ドキュメント

- [LLM統合](@.claude/rules/04-llm-integration.md) - Ollama連携パターン
- [プロジェクト概要](@.claude/rules/00-overview.md) - 4ステップの処理フロー
