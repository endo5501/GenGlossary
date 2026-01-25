---
priority: 2
tags: [db, extractor, cli]
description: "Extend term extraction to optionally return categories and save them to terms_extracted."
created_at: "2026-01-23T12:12:24Z"
started_at: 2026-01-25T08:05:59Z # Do not modify manually
closed_at: 2026-01-25T09:43:32Z # Do not modify manually
---

# Ticket Overview

Implement plan B with a behavior change: store all classified terms (including `common_noun`) in `terms_extracted`, and defer skipping `common_noun` until provisional glossary generation. Extend `TermExtractor.extract_terms()` to optionally return term+category pairs without breaking the current API.


## Tasks

- [x] Define return type for category-enabled extraction (new model or typed dict)
- [x] Update `TermExtractor.extract_terms()` signature to support `return_categories` and include `common_noun` when requested
- [x] Adjust provisional glossary flow to skip `common_noun` at generation time (not at extraction time)
- [x] Wire category-aware returns into `src/genglossary/cli.py` (save all categories to DB)
- [x] Wire category-aware returns into `src/genglossary/cli_db.py` (save all categories to DB)
- [x] Add/adjust tests for category persistence and `common_noun` skipping behavior
- [x] Code simplification review using code-simplifier agent
- [x] Update docs/architecture.md
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing


## Notes

Keep backward compatibility for callers that expect `list[str]`.
Avoid duplicate LLM calls; reuse the classification results already produced in extraction.

## Review Notes (2026-01-25)

### Findings

- **High**: `return_categories=True` path no longer deduplicates terms before DB insert. Duplicate terms from LLM classification can trigger `sqlite3.IntegrityError` due to `terms_extracted.term_text` UNIQUE, aborting the run and leaving partial data. Consider deduping in `_get_classified_terms` or handling duplicates on insert.
- **Low**: CLI progress total can be inaccurate with categories because `GlossaryGenerator` filters `common_noun` by default; progress may not reach 100%.

### Questions

- Should duplicate classifications be resolved by “first wins”, “last wins”, or should category conflicts be reported?
