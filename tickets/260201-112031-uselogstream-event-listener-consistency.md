---
priority: 7
tags: [frontend, refactoring]
description: "useLogStream: Unify event listener registration to addEventListener"
created_at: "2026-02-01T11:20:31Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# useLogStream: Unify event listener registration

## Overview

`useLogStream` hook uses mixed approaches for event listener registration:
- `onopen`, `onmessage`, `onerror` use property assignment
- `complete` event uses `addEventListener`

This inconsistency makes the code harder to maintain. Unifying to `addEventListener` for all events would improve consistency and clarity.

## Current Implementation

```typescript
eventSource.onopen = handleOpen
eventSource.onmessage = handleMessage
eventSource.addEventListener('complete', handleComplete)  // Inconsistent!
eventSource.onerror = handleError
```

## Proposed Implementation

```typescript
eventSource.addEventListener('open', handleOpen)
eventSource.addEventListener('message', handleMessage)
eventSource.addEventListener('complete', handleComplete)
eventSource.addEventListener('error', handleError)

return disconnect  // eventSource.close() handles all cleanup
```

## Target File

- `frontend/src/api/hooks/useLogStream.ts`

## Tasks

- [ ] TDD: Write tests for event listener consistency
- [ ] Refactor to use addEventListener for all events
- [ ] Commit
- [ ] Run tests (`pnpm test`) before reviewing and pass all tests (No exceptions)
- [ ] Code simplification review using code-simplifier agent
- [ ] Run tests (`pnpm test`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## Notes

- Discovered during code-simplifier review of 260201-075029-uselogstream-event-listener-cleanup ticket
- Low priority as current implementation works correctly
- Pure refactoring, no functional change expected
