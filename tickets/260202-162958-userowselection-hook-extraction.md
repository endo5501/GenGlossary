---
priority: 1
tags: [frontend, refactoring]
description: "Extract common row selection logic into useRowSelection hook"
created_at: "2026-02-02T16:29:58Z"
started_at: 2026-02-04T14:14:06Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# Extract useRowSelection Hook

## Overview

Multiple pages have duplicated row selection logic (onClick, onKeyDown, aria-selected, styles). This should be extracted into a reusable hook.

## Affected Files

- ProvisionalPage.tsx (Table.Tr, lines 93-110)
- RefinedPage.tsx (Paper, lines 68-87)
- IssuesPage.tsx (Paper, lines 79-98)

**Note:** FilesPage.tsx is excluded - it uses navigation instead of selection.

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
- [ ] Commit
- [ ] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [ ] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Update docs/architecture/*.md
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing


## Design Decisions (Brainstorming 2026-02-04)

1. **FilesPageは除外** - 選択ではなくナビゲーション動作のため対象外
2. **Mantine固有の`bg`をそのまま返す** - プロジェクト全体がMantine使用のため
3. **`frontend/src/hooks/` を新規作成** - 将来の拡張性を考慮

## Test Plan

- `onClick` が正しいIDで `onSelect` を呼ぶ
- Enter/Spaceキーで `onSelect` が呼ばれる
- 他のキーでは何も起きない
- 選択状態で `aria-selected: true` と `bg` が設定される
- 非選択状態で `aria-selected: false` と `bg: undefined`

## Notes

- Identified during code-simplifier review of PageContainer refactoring
