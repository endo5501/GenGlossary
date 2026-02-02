---
priority: 3
tags: [refactoring, code-quality]
description: "Code simplification: FileDetailResponse inheritance and DocumentViewer utilities"
created_at: "2026-02-01T12:01:33Z"
started_at: 2026-02-02T13:08:14Z # Do not modify manually
closed_at: 2026-02-02T13:17:07Z # Do not modify manually
---

# Code Simplification: FileDetailResponse and DocumentViewer

## Overview

Code simplification opportunities identified during Document Viewer implementation review.
These are low-priority improvements for code maintainability.

## Tasks

- [x] Python: Make `FileDetailResponse` inherit from `FileResponse` to eliminate code duplication
- [x] TypeScript: Extract `findTermData` function from `DocumentViewerPage.tsx` to a utility file
- [x] ~~TypeScript: Simplify badge logic in `TermCard.tsx`~~ (Skipped: current ternary is sufficient for 2 states)
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [x] Get developer approval before closing

## Design

### Task 1: Python - FileDetailResponse Inheritance

**File**: `src/genglossary/api/schemas/file_schemas.py`

Change `FileDetailResponse` to inherit from `FileResponse`:
```python
class FileDetailResponse(FileResponse):
    content: str = Field(..., description="File content")
```

Update `from_db_row` to call parent and add `content`.

### Task 2: TypeScript - Extract findTermData

**New file**: `frontend/src/utils/termUtils.ts`

```typescript
import type { GlossaryTermResponse } from '../api/types'

export function findTermData(
  termList: GlossaryTermResponse[],
  termText: string
): GlossaryTermResponse | null {
  return termList.find(
    (t) => t.term_name.toLowerCase() === termText.toLowerCase()
  ) ?? null
}
```

Update `DocumentViewerPage.tsx` to import and use this utility.

## Notes

- These are "nice-to-have" improvements, not critical issues
- All functionality is working correctly without these changes
- Identified during code-simplifier review of Document Viewer implementation
