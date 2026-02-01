---
priority: 8
tags: [refactoring, code-quality]
description: "Code simplification: FileDetailResponse inheritance and DocumentViewer utilities"
created_at: "2026-02-01T12:01:33Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# Code Simplification: FileDetailResponse and DocumentViewer

## Overview

Code simplification opportunities identified during Document Viewer implementation review.
These are low-priority improvements for code maintainability.

## Tasks

- [ ] Python: Make `FileDetailResponse` inherit from `FileResponse` to eliminate code duplication
- [ ] TypeScript: Extract `findTermData` function from `DocumentViewerPage.tsx` to a utility file
- [ ] TypeScript: Simplify badge logic in `TermCard.tsx` using object map instead of repeated ternary operators
- [ ] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## Notes

- These are "nice-to-have" improvements, not critical issues
- All functionality is working correctly without these changes
- Identified during code-simplifier review of Document Viewer implementation
