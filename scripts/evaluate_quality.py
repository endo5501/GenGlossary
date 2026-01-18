#!/usr/bin/env python3
"""Evaluate glossary generation quality with optimized prompts."""

import time
from pathlib import Path

from genglossary.config import Config
from genglossary.document_loader import DocumentLoader
from genglossary.glossary_generator import GlossaryGenerator
from genglossary.glossary_refiner import GlossaryRefiner
from genglossary.glossary_reviewer import GlossaryReviewer
from genglossary.llm.ollama_client import OllamaClient
from genglossary.output.markdown_writer import MarkdownWriter
from genglossary.term_extractor import TermExtractor


def main() -> None:
    """Evaluate glossary generation quality and performance."""
    print("=" * 80)
    print("Glossary Generation Quality Evaluation")
    print("=" * 80)
    print()

    # Configuration
    input_file = "target_docs/sample_story.md"
    output_file = "output/evaluation_glossary.md"

    # Check if Ollama is available
    config = Config()
    print(f"Model: {config.ollama_model}")
    print(f"Base URL: {config.ollama_base_url}")
    print()

    # Load document
    print(f"Loading document: {input_file}")
    loader = DocumentLoader()
    documents = loader.load_documents([input_file])
    print(f"  Loaded {len(documents)} document(s)")
    print()

    # Initialize LLM client
    llm_client = OllamaClient(base_url=config.ollama_base_url, model=config.ollama_model)

    # Measure overall time
    start_time = time.time()

    # Step 1: Term Extraction
    print("Step 1: Extracting terms...")
    extractor = TermExtractor(llm_client=llm_client)

    extraction_start = time.time()
    analysis = extractor.analyze_extraction(documents)
    extraction_time = time.time() - extraction_start

    print(f"  Pre-filter candidates: {analysis.pre_filter_candidate_count}")
    print(f"  Post-filter candidates: {analysis.post_filter_candidate_count}")
    print(f"  Approved terms: {len(analysis.llm_approved)}")
    print(f"  Rejected terms: {len(analysis.llm_rejected)}")
    print(f"  Extraction time: {extraction_time:.2f}s")
    print()

    # Display classification results
    print("  Classification by category:")
    for category, terms in analysis.classification_results.items():
        if terms:
            print(f"    {category}: {len(terms)} terms")
            print(f"      → {', '.join(terms[:5])}")
            if len(terms) > 5:
                print(f"      ... and {len(terms) - 5} more")
    print()

    # Step 2: Glossary Generation
    print("Step 2: Generating glossary...")
    generator = GlossaryGenerator(llm_client=llm_client)

    generation_start = time.time()
    glossary = generator.generate(analysis.llm_approved, documents)
    generation_time = time.time() - generation_start

    print(f"  Generated {glossary.term_count} definitions")
    print(f"  Generation time: {generation_time:.2f}s")
    print()

    # Step 3: Review
    print("Step 3: Reviewing glossary...")
    reviewer = GlossaryReviewer(llm_client=llm_client)

    review_start = time.time()
    issues = reviewer.review(glossary)
    review_time = time.time() - review_start

    print(f"  Found {len(issues)} issues")
    print(f"  Review time: {review_time:.2f}s")

    # Display issues by type
    if issues:
        print()
        print("  Issues by type:")
        issue_types = {}
        exclusions = []
        for issue in issues:
            if issue.should_exclude:
                exclusions.append(issue.term_name)
            else:
                issue_types.setdefault(issue.issue_type, []).append(issue.term_name)

        for issue_type, terms in issue_types.items():
            print(f"    {issue_type}: {len(terms)} terms")
            print(f"      → {', '.join(terms[:3])}")
            if len(terms) > 3:
                print(f"      ... and {len(terms) - 3} more")

        if exclusions:
            print(f"    should_exclude: {len(exclusions)} terms")
            print(f"      → {', '.join(exclusions[:3])}")
            if len(exclusions) > 3:
                print(f"      ... and {len(exclusions) - 3} more")
    print()

    # Step 4: Refinement
    print("Step 4: Refining glossary...")
    refiner = GlossaryRefiner(llm_client=llm_client)

    refinement_start = time.time()
    refined_glossary = refiner.refine(glossary, issues, documents)
    refinement_time = time.time() - refinement_start

    print(f"  Final glossary: {refined_glossary.term_count} terms")
    if "excluded_terms" in refined_glossary.metadata:
        excluded = refined_glossary.metadata["excluded_terms"]
        print(f"  Excluded: {len(excluded)} terms")
    print(f"  Refinement time: {refinement_time:.2f}s")
    print()

    # Write output
    print(f"Writing glossary to: {output_file}")
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    writer = MarkdownWriter()
    writer.write(refined_glossary, output_file)
    print()

    # Summary
    total_time = time.time() - start_time
    print("=" * 80)
    print("Performance Summary")
    print("=" * 80)
    print(f"Term Extraction:    {extraction_time:>8.2f}s ({extraction_time/total_time*100:>5.1f}%)")
    print(f"Glossary Generation: {generation_time:>8.2f}s ({generation_time/total_time*100:>5.1f}%)")
    print(f"Review:             {review_time:>8.2f}s ({review_time/total_time*100:>5.1f}%)")
    print(f"Refinement:         {refinement_time:>8.2f}s ({refinement_time/total_time*100:>5.1f}%)")
    print(f"{'Total:':<20} {total_time:>8.2f}s")
    print()

    # Quality metrics
    print("=" * 80)
    print("Quality Metrics")
    print("=" * 80)
    print(f"Extraction Precision: {len(analysis.llm_approved)}/{analysis.post_filter_candidate_count} = {len(analysis.llm_approved)/analysis.post_filter_candidate_count*100:.1f}%")
    print(f"Final Terms:          {refined_glossary.term_count}")

    if refined_glossary.term_count > 0:
        avg_confidence = sum(term.confidence for term in refined_glossary.terms.values()) / refined_glossary.term_count
        print(f"Average Confidence:   {avg_confidence:.2f}")

    print()
    print(f"✅ Evaluation complete! Check the output at: {output_file}")
    print()


if __name__ == "__main__":
    main()
