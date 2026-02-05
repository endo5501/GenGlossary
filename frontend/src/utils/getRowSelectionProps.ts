import type { KeyboardEvent, CSSProperties } from 'react'

export interface RowSelectionProps {
  onClick: () => void
  onKeyDown: (e: KeyboardEvent) => void
  tabIndex: number
  'aria-selected': boolean
  style: CSSProperties
  bg: string | undefined
}

export function getRowSelectionProps<T extends { id: number }>(
  item: T,
  selectedId: number | null,
  onSelect: (id: number) => void
): RowSelectionProps {
  return {
    onClick: () => onSelect(item.id),
    onKeyDown: (e: KeyboardEvent) => {
      if (e.key === 'Enter' || e.key === ' ' || e.key === 'Spacebar') {
        e.preventDefault()
        onSelect(item.id)
      }
    },
    tabIndex: 0,
    'aria-selected': selectedId === item.id,
    style: { cursor: 'pointer' },
    bg: selectedId === item.id ? 'var(--mantine-color-blue-light)' : undefined,
  }
}
