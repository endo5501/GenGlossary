---
priority: 2
tags: [performance, document-viewer]
description: "Document Viewer performance optimization and error handling"
created_at: "2026-02-01T12:03:25Z"
started_at: 2026-02-05T13:51:16Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# Document Viewer Performance Optimization

## Overview

Performance and robustness improvements for Document Viewer identified during Codex review.

## Tasks

- [x] Backend: Add file size limit or pagination for large documents to prevent memory issues
- [x] Frontend: Optimize term highlighting regex for large term lists (precompute map/set, memoize)
- [x] Frontend: Add error UI for failed queries (files, terms, file detail) with retry option
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## Notes

- Main risks: unbounded content/regex sizes
- Current implementation works fine for typical document sizes
- Identified during Codex MCP code review

---

## Design: Backend File Size Limit (3MB)

### Summary

Add content size validation to prevent memory issues from large document uploads.

### Implementation

**File**: `src/genglossary/api/routers/files.py`

1. **Add constant**
   ```python
   MAX_CONTENT_BYTES = 3 * 1024 * 1024  # 3MB
   ```

2. **Add validation function**
   ```python
   def _validate_content_size(content: str) -> None:
       content_bytes = len(content.encode("utf-8"))
       if content_bytes > MAX_CONTENT_BYTES:
           raise HTTPException(
               status_code=status.HTTP_400_BAD_REQUEST,
               detail=f"Content too large ({content_bytes} bytes). Max: {MAX_CONTENT_BYTES} bytes (3MB)",
           )
   ```

3. **Apply to endpoints**
   - `create_file`: Check after file name validation
   - `create_files_bulk`: Check each file

### Error Response

- HTTP 400 Bad Request
- Message: `"Content too large (X bytes). Max: 3145728 bytes (3MB)"`
