---
priority: 5
tags: [frontend, refactoring, code-quality]
description: "PageContainer and layout code simplification"
created_at: "2026-02-01T22:30:50Z"
started_at: 2026-02-02T16:19:55Z # Do not modify manually
closed_at: 2026-02-02T16:35:29Z # Do not modify manually
---

# PageContainer and Layout Code Simplification

## Overview

Code simplification review identified several opportunities to improve the layout code in frontend components.

## Issues Identified

### 1. PageContainer Duplicate Layout Code (HIGH)

The same layout structure is duplicated 3 times in PageContainer.tsx for error, empty, and normal states:

```tsx
<Box style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
  <Group data-testid="action-bar" p="md" style={{ flexShrink: 0, ... }}>
    {actionBar}
  </Group>
  {/* different content */}
</Box>
```

### 2. FilesPage Not Using PageContainer (HIGH)

FilesPage implements its own layout pattern instead of reusing PageContainer.

### 3. Duplicated Style Definitions (MEDIUM)

Same style patterns scattered across multiple files:
- `{ height: '100%', display: 'flex', flexDirection: 'column' }`
- `{ flex: 1, overflowY: 'auto', minHeight: 0 }`

### 4. Magic Numbers (MEDIUM)

- Header height (60px) hardcoded in multiple places
- Should use constants or theme variables

## Tasks

- [x] Extract common layout styles to a shared file
- [x] Refactor PageContainer to eliminate duplicate code
- [x] Migrate FilesPage to use PageContainer
- [x] Extract HEADER_HEIGHT constant
- [x] Commit
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Update docs/architecture/*.md
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing


## Design

### File Structure

```
frontend/src/
├── styles/
│   └── layout.css          # New: common layout styles + CSS variables
├── components/
│   └── common/
│       └── PageContainer.tsx  # Modified: add render props, use CSS classes
└── pages/
    └── FilesPage.tsx         # Modified: migrate to PageContainer
```

### 1. layout.css (New)

```css
:root {
  --header-height: 60px;
}

.page-layout {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.scrollable-content {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
  padding: var(--mantine-spacing-md);
}

.action-bar {
  flex-shrink: 0;
  border-bottom: 1px solid var(--mantine-color-gray-3);
}
```

### 2. PageContainer Refactoring

- Add optional render props: `renderLoading`, `renderEmpty`, `renderError`
- Extract common layout to `renderContent` helper function
- Use CSS classes instead of inline styles
- Maintain backward compatibility (existing pages unchanged)

```tsx
interface PageContainerProps {
  // ... existing props ...
  renderLoading?: () => ReactNode
  renderEmpty?: () => ReactNode
  renderError?: (error: Error, onRetry?: () => void) => ReactNode
}
```

### 3. FilesPage Migration

- Remove custom layout code
- Use PageContainer with render props for custom loading/empty states
- Preserve existing UI behavior via `renderLoading` and `renderEmpty`

### 4. CSS Variable Replacement

- `AppShell.tsx`: Replace `60` with `var(--header-height)`
- `DocumentViewerPage.tsx`: Replace `60px` with `var(--header-height)`
- `main.tsx`: Add `import './styles/layout.css'`

## Notes

- Original issue found during code review of fixed header/footer layout ticket
- Consider using Mantine's createStyles or theme for consistent styling
