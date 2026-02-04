---
priority: 2
tags: [performance, document-viewer]
description: "Document Viewer performance optimization and error handling"
created_at: "2026-02-01T12:03:25Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# Document Viewer Performance Optimization

## Overview

Performance and robustness improvements for Document Viewer identified during Codex review.

## Tasks

- [ ] Backend: Add file size limit or pagination for large documents to prevent memory issues
- [ ] Frontend: Optimize term highlighting regex for large term lists (precompute map/set, memoize)
- [ ] Frontend: Add error UI for failed queries (files, terms, file detail) with retry option
- [ ] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## Notes

- Main risks: unbounded content/regex sizes
- Current implementation works fine for typical document sizes
- Identified during Codex MCP code review
