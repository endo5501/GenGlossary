export function getRowSelectionProps<T extends { id: number }>(
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
    'aria-selected': selectedId === item.id,
    style: { cursor: 'pointer' },
    bg: selectedId === item.id ? 'var(--mantine-color-blue-light)' : undefined,
  }
}
