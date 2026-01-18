#!/usr/bin/env python3
"""Measure token counts for all component prompts."""

from genglossary.models.document import Document
from genglossary.models.glossary import Glossary, GlossaryIssue
from genglossary.models.term import Term, TermOccurrence
from genglossary.utils.token_counter import TokenCounter


def create_sample_document() -> Document:
    """Create a sample document for testing."""
    content = """量子コンピュータは、量子力学の原理を利用して計算を行うコンピュータです。
従来のコンピュータが0と1のビットで情報を扱うのに対し、量子コンピュータは
量子ビット（キュービット）を使用します。キュービットは0と1の状態を
同時に保持する重ね合わせという性質を持ちます。

量子コンピュータの最大の特徴は、量子もつれという現象を利用した並列計算です。
これにより、特定の問題では従来のコンピュータを遥かに上回る計算速度を
実現できます。"""
    return Document(file_path="sample.txt", content=content)


def create_sample_glossary() -> Glossary:
    """Create a sample glossary for testing."""
    glossary = Glossary()
    glossary.add_term(
        Term(
            name="量子コンピュータ",
            definition="量子力学の原理を利用して計算を行うコンピュータ",
            occurrences=[
                TermOccurrence(document_path="sample.txt", line_number=1, context="量子コンピュータは..."),
                TermOccurrence(document_path="sample.txt", line_number=2, context="従来のコンピュータが..."),
                TermOccurrence(document_path="sample.txt", line_number=5, context="量子コンピュータの..."),
            ],
            confidence=0.9,
        )
    )
    glossary.add_term(
        Term(
            name="量子ビット",
            definition="量子コンピュータで情報を扱う基本単位",
            occurrences=[
                TermOccurrence(document_path="sample.txt", line_number=3, context="量子ビット（キュービット）を使用します。"),
            ],
            confidence=0.85,
        )
    )
    return glossary


def create_sample_issues() -> list[GlossaryIssue]:
    """Create sample issues for testing."""
    return [
        GlossaryIssue(
            term_name="量子コンピュータ",
            issue_type="unclear",
            description="定義が不完全です。",
        ),
    ]


def measure_term_extractor() -> dict[str, int]:
    """Measure TermExtractor prompt token count."""
    # Reconstruct the batch classification prompt
    terms = ["量子コンピュータ", "量子ビット", "重ね合わせ", "量子もつれ"]
    terms_text = "\n".join(f"- {term}" for term in terms)
    document = create_sample_document()

    CATEGORY_DEFINITIONS = """## カテゴリ定義

1. **person_name（人名）**: 架空・実在の人物名
   例: ガウス卿、田中太郎、アリス

2. **place_name（地名）**: 国名、都市名、地域名、場所の名前
   例: エデルト、アソリウス島、東京

3. **organization（組織・団体名）**: 騎士団、軍隊、企業、団体など
   例: アソリウス島騎士団、エデルト軍、近衛騎士団

4. **title（役職・称号）**: 王子、騎士団長、将軍などの役職や称号
   例: 騎士団長、騎士代理爵位、将軍

5. **technical_term（技術用語・専門用語）**: この文脈特有の専門用語
   例: 聖印、魔神討伐、魔神代理領

6. **common_noun（一般名詞）**: 辞書的意味で理解できる一般的な名詞
   例: 未亡人、行方不明、方角、重要"""

    prompt = f"""あなたは用語分類の専門家です。
以下の用語を各々1つのカテゴリに分類してください。

## 分類対象の用語:
{terms_text}

{CATEGORY_DEFINITIONS}

## Few-shot Examples

### 正しい分類の例

**入力:** ["ガウス卿", "アソリウス島", "アソリウス島騎士団", "騎士団長", "聖印", "未亡人", "偵察"]

**出力:**
- ガウス卿 → person_name (人物の固有名)
- アソリウス島 → place_name (地名)
- アソリウス島騎士団 → organization (組織名)
- 騎士団長 → title (役職)
- 聖印 → technical_term (この作品固有の概念)
- 未亡人 → common_noun (一般的な辞書語)
- 偵察 → common_noun (一般的な軍事用語)

### 重要な判断基準

1. **作品固有の概念** → technical_term
   - 聖印、魔神討伐、魔神代理領 など

2. **一般的な辞書語** → common_noun
   - 未亡人、行方不明、方角、偵察 など

3. **組織は完全形で分類**
   - "アソリウス島騎士団" → organization
   - "近衛騎士団" → organization

## 注意事項
- 各用語を必ず1つのカテゴリに分類してください
- 用語集に載せるべきかどうかを基準に判断してください
- 迷った場合は、文脈固有の意味を持つかどうかを基準にしてください

JSON形式で回答してください:
{{"classifications": [
  {{"term": "用語1", "category": "カテゴリ名"}},
  {{"term": "用語2", "category": "カテゴリ名"}}
]}}

カテゴリ名は person_name, place_name, organization, title, technical_term, common_noun のいずれかです。
すべての用語を分類してください。"""

    counter = TokenCounter()
    return counter.count(prompt)


def measure_glossary_generator() -> dict[str, int]:
    """Measure GlossaryGenerator prompt token count."""
    # Reconstruct the definition generation prompt
    term = "量子コンピュータ"
    contexts = [
        "- 量子コンピュータは、量子力学の原理を利用して計算を行うコンピュータです。",
        "- 従来のコンピュータが0と1のビットで情報を扱うのに対し、量子コンピュータは",
    ]
    context_text = "\n".join(contexts)

    prompt = f"""用語: {term}
出現箇所とコンテキスト:
{context_text}

## Few-shot Examples

### 良い定義の例

**用語:** アソリウス島騎士団
**定義:** エデルト王国の辺境、アソリウス島を守る騎士団。魔神討伐の最前線として重要な役割を担う。
**信頼度:** 0.9

**用語:** 聖印
**定義:** 騎士が魔神討伐に参加するために必要な特別な力の印。これを持つ者だけが魔神と戦える。
**信頼度:** 0.85

### 避けるべき定義の例

❌ **用語:** 騎士団長
❌ **定義:** 騎士団のリーダー
❌ **理由:** 一般的すぎる。この文脈での具体的な役割や特徴を説明すべき。

✅ **改善例:** アソリウス島騎士団を率いる指導者。騎士代理爵位を持ち、魔神討伐の指揮を執る。

## 重要な指針

1. **文脈固有の意味を説明する**
   - 辞書的な定義ではなく、このドキュメントでの使われ方を説明
   - 出現箇所のコンテキストを活用して具体的に記述

2. **簡潔かつ明確に**
   - 1-2文で要点を伝える
   - 専門用語は避け、分かりやすい言葉で説明

3. **信頼度の基準**
   - 0.8-1.0: 複数の出現箇所から明確に意味が分かる
   - 0.5-0.7: 出現箇所が少ないが、ある程度意味が推測できる
   - 0.0-0.4: 出現箇所が不足、または意味が不明確

このドキュメント固有の使われ方を説明してください。
JSON形式で回答してください: {{"definition": "...", "confidence": 0.0-1.0}}"""

    counter = TokenCounter()
    return counter.count(prompt)


def measure_glossary_reviewer() -> dict[str, int]:
    """Measure GlossaryReviewer prompt token count."""
    # Need to read the actual prompt from GlossaryReviewer
    # For now, create a placeholder based on the expected structure
    glossary = create_sample_glossary()

    # Reconstruct the review prompt (simplified version)
    entries_text = "\n\n".join([
        f"**{term.name}**\n定義: {term.definition}\n出現: {', '.join(str(occ.line_number) for occ in term.occurrences)}"
        for term in glossary.terms.values()
    ])

    prompt = f"""あなたは用語集の精査を行う専門家です。
以下の暫定用語集を精査し、問題点を列挙してください。

## 暫定用語集:
{entries_text}

## Few-shot Examples

### 良い精査の例

**用語集:**
- **アソリウス島**: エデルトの島
- **騎士団長**: 騎士団のトップ

**問題点:**
1. アソリウス島: 「エデルトの島」では不十分。具体的な位置や役割を説明すべき。(unclear)
2. 騎士団長: どの騎士団の団長か不明。「アソリウス島騎士団長」と明確にすべき。(unclear)

## 精査基準

以下の観点で問題点を列挙してください:

1. **unclear（不明瞭）**: 定義が曖昧、または詳細が不足
2. **contradiction（矛盾）**: 用語間で矛盾がある
3. **missing（欠落）**: 重要な情報が欠けている

JSON形式で回答してください:
{{"issues": [
  {{"term": "用語名", "issue_type": "unclear/contradiction/missing", "description": "問題の説明"}}
]}}"""

    counter = TokenCounter()
    return counter.count(prompt)


def measure_glossary_refiner() -> dict[str, int]:
    """Measure GlossaryRefiner prompt token count."""
    glossary = create_sample_glossary()
    issues = create_sample_issues()
    document = create_sample_document()

    # Reconstruct the refinement prompt (simplified version)
    entries_text = "\n\n".join([
        f"**{term.name}**\n定義: {term.definition}"
        for term in glossary.terms.values()
    ])

    issues_text = "\n".join([
        f"- {issue.term_name}: {issue.description} (タイプ: {issue.issue_type})"
        for issue in issues
    ])

    prompt = f"""あなたは用語集の改善を行う専門家です。
以下の問題点に基づいて、暫定用語集をブラッシュアップしてください。

## 暫定用語集:
{entries_text}

## 問題点リスト:
{issues_text}

## Few-shot Examples

### 改善前の用語集と問題点

**用語:** アソリウス島騎士団
**定義:** 騎士団
**問題点:** 定義が曖昧で具体性に欠ける (unclear)

### 改善後の用語集

**用語:** アソリウス島騎士団
**定義:** エデルト王国の辺境、アソリウス島を守る騎士団。魔神討伐の最前線として重要な役割を担う。

## 改善指針

1. **具体性を高める**: 曖昧な表現を避け、文脈固有の詳細を追加
2. **矛盾を解消**: 用語間の整合性を確保
3. **欠落情報を補完**: ドキュメントから重要な情報を抽出して追加

## ドキュメント:
{document.content}

問題点を解決した改善版の用語集をJSON形式で回答してください:
{{"entries": [
  {{"term": "用語名", "definition": "改善された定義"}}
]}}"""

    counter = TokenCounter()
    return counter.count(prompt)


def main() -> None:
    """Measure all prompts and display results."""
    print("=" * 80)
    print("Prompt Token Count Measurement")
    print("=" * 80)
    print()

    components = [
        ("TermExtractor", measure_term_extractor),
        ("GlossaryGenerator", measure_glossary_generator),
        ("GlossaryReviewer", measure_glossary_reviewer),
        ("GlossaryRefiner", measure_glossary_refiner),
    ]

    results = {}
    for name, measure_func in components:
        print(f"Measuring {name}...")
        metrics = measure_func()
        results[name] = metrics

        print(f"  Characters: {metrics['characters']:,}")
        print(f"  Words: {metrics['words']:,}")
        print(f"  Lines: {metrics['lines']:,}")
        print(f"  Estimated Tokens: {metrics['estimated_tokens']:,}")
        print()

    # Summary
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    total_chars = sum(r["characters"] for r in results.values())
    total_tokens = sum(r["estimated_tokens"] for r in results.values())

    print(f"Total Characters: {total_chars:,}")
    print(f"Total Estimated Tokens: {total_tokens:,}")
    print()

    # Save to file
    output_file = "prompt_baseline.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("Prompt Token Count Baseline\n")
        f.write("=" * 80 + "\n\n")
        for name, metrics in results.items():
            f.write(f"{name}:\n")
            f.write(f"  Characters: {metrics['characters']:,}\n")
            f.write(f"  Words: {metrics['words']:,}\n")
            f.write(f"  Lines: {metrics['lines']:,}\n")
            f.write(f"  Estimated Tokens: {metrics['estimated_tokens']:,}\n\n")

        f.write("\nSummary:\n")
        f.write(f"Total Characters: {total_chars:,}\n")
        f.write(f"Total Estimated Tokens: {total_tokens:,}\n")

    print(f"Results saved to {output_file}")


if __name__ == "__main__":
    main()
