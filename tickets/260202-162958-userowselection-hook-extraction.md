---
priority: 1
tags: [frontend, refactoring]
description: "Extract common row selection logic into useRowSelection hook"
created_at: "2026-02-02T16:29:58Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# Extract useRowSelection Hook

## Overview

Multiple pages have duplicated row selection logic (onClick, onKeyDown, aria-selected, styles). This should be extracted into a reusable hook.

## Affected Files

- ProvisionalPage.tsx
- RefinedPage.tsx
- IssuesPage.tsx
- FilesPage.tsx

## Current Duplicated Pattern

```tsx
onClick={() => setSelectedId(entry.id)}
onKeyDown={(e) => {
  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault()
    setSelectedId(entry.id)
  }
}}
tabIndex={0}
role="button"
aria-selected={selectedId === entry.id}
style={{ cursor: 'pointer' }}
bg={selectedId === entry.id ? 'var(--mantine-color-blue-light)' : undefined}
```

## Proposed Solution

Create `hooks/useRowSelection.ts`:

```tsx
export function useRowSelection<T extends { id: number }>(
  item: T,
  selectedId: number | null,
  onSelect: (id: number) => void
) {
  return {
    onClick: () => onSelect(item.id),
    onKeyDown: (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault()
        onSelect(item.id)
      }
    },
    tabIndex: 0,
    role: 'button' as const,
    'aria-selected': selectedId === item.id,
    style: { cursor: 'pointer' },
    bg: selectedId === item.id ? 'var(--mantine-color-blue-light)' : undefined,
  }
}
```

## Tasks

- [ ] Create useRowSelection hook
- [ ] Add tests for the hook
- [ ] Migrate ProvisionalPage to use hook
- [ ] Migrate RefinedPage to use hook
- [ ] Migrate IssuesPage to use hook
- [ ] Migrate FilesPage to use hook
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

- Identified during code-simplifier review of PageContainer refactoring
