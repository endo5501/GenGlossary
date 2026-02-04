---
priority: 3
tags: [frontend, refactoring]
description: "Rename useRowSelection to getRowSelectionProps"
created_at: "2026-02-04T14:48:23Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# Rename useRowSelection to getRowSelectionProps

## Overview

`useRowSelection` is named like a React hook but doesn't actually use any React hooks internally. This is misleading for maintainers who expect "use*" functions to follow React hook rules.

Identified during code-simplifier and codex MCP review of ticket 260202-162958-userowselection-hook-extraction.

## Proposed Changes

1. Rename `useRowSelection` → `getRowSelectionProps`
2. Move from `hooks/` to `utils/` directory
3. Update all imports in consuming components

## Affected Files

- `frontend/src/hooks/useRowSelection.ts` → `frontend/src/utils/getRowSelectionProps.ts`
- `frontend/src/__tests__/useRowSelection.test.ts` → `frontend/src/__tests__/getRowSelectionProps.test.ts`
- `frontend/src/pages/ProvisionalPage.tsx`
- `frontend/src/pages/RefinedPage.tsx`
- `frontend/src/pages/IssuesPage.tsx`

## Tasks

- [ ] Rename function and file
- [ ] Move to utils directory
- [ ] Update test file
- [ ] Update all imports
- [ ] Commit
- [ ] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [ ] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Update docs/architecture/*.md
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing


## Notes

- Low priority refactoring task
- No functional changes, only naming convention improvement
