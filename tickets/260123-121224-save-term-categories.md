---
priority: 2
tags: [db, extractor, cli]
description: "Extend term extraction to optionally return categories and save them to terms_extracted."
created_at: "2026-01-23T12:12:24Z"
started_at: 2026-01-25T08:05:59Z # Do not modify manually
closed_at: null   # Do not modify manually
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
- [ ] Code simplification review using code-simplifier agent
- [x] Update docs/architecture.md
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing


## Notes

Keep backward compatibility for callers that expect `list[str]`.
Avoid duplicate LLM calls; reuse the classification results already produced in extraction.
