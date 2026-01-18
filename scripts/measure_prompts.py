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

    CATEGORY_DEFINITIONS = """## カテゴリ
1. person_name: 人名（例: ガウス卿）
2. place_name: 地名（例: アソリウス島）
3. organization: 組織・団体（例: 騎士団）
4. title: 役職・称号（例: 団長）
5. technical_term: 専門用語（例: 聖印）
6. common_noun: 一般名詞（例: 未亡人）"""

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

各用語を1カテゴリに分類。迷う場合は文脈固有性で判断。

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

**用語:** アソリウス島騎士団
**定義:** エデルト王国の辺境、アソリウス島を守る騎士団。魔神討伐の最前線として重要な役割を担う。
**信頼度:** 0.9

文脈固有の意味を1-2文で説明。信頼度: 明確=0.8+, 推測可能=0.5-0.7, 不明確=0.0-0.4

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

    prompt = f"""用語: 量子コンピュータ
現在の定義: {glossary.get_term("量子コンピュータ").definition if glossary.get_term("量子コンピュータ") else "未定義"}
問題点: 定義が不完全です。
問題タイプ: unclear

追加コンテキスト:
{document.content}

## Few-shot Examples

### 改善例1: 不明確な定義の改善 (unclear)

**用語:** 騎士団長
**現在の定義:** 騎士団のリーダー
**問題点:** 定義が一般的すぎる。この文脈での具体的な役割を説明すべき。
**改善された定義:** アソリウス島騎士団を率いる指導者。騎士代理爵位を持ち、魔神討伐の指揮を執る。
**信頼度:** 0.85

### 改善例2: 関連性の欠落の改善 (missing_relation)

**用語:** 聖印
**現在の定義:** 特別な力の印
**問題点:** 関連用語（魔神討伐、騎士）との関係が不明確
**改善された定義:** 騎士が魔神討伐に参加するために必要な特別な力の印。これを持つ者だけが魔神と戦える。
**信頼度:** 0.9

問題タイプに応じて改善し、コンテキストを活用して具体的な定義を作成してください。

JSON形式で回答してください:
{{"refined_definition": "改善された定義", "confidence": 0.0-1.0}}"""

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
