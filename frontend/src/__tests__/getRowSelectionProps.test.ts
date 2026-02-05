import { describe, expect, it, vi } from 'vitest'
import { getRowSelectionProps } from '../utils/getRowSelectionProps'

describe('getRowSelectionProps', () => {
  const mockItem = { id: 1, name: 'Test Item' }
  const mockOnSelect = vi.fn()

  beforeEach(() => {
    mockOnSelect.mockClear()
  })

  describe('onClick', () => {
    it('should call onSelect with item id when clicked', () => {
      const props = getRowSelectionProps(mockItem, null, mockOnSelect)

      props.onClick()

      expect(mockOnSelect).toHaveBeenCalledWith(1)
      expect(mockOnSelect).toHaveBeenCalledTimes(1)
    })
  })

  describe('onKeyDown', () => {
    it('should call onSelect when Enter key is pressed', () => {
      const props = getRowSelectionProps(mockItem, null, mockOnSelect)

      const event = {
        key: 'Enter',
        preventDefault: vi.fn(),
      } as unknown as React.KeyboardEvent

      props.onKeyDown(event)

      expect(event.preventDefault).toHaveBeenCalled()
      expect(mockOnSelect).toHaveBeenCalledWith(1)
    })

    it('should call onSelect when Space key is pressed', () => {
      const props = getRowSelectionProps(mockItem, null, mockOnSelect)

      const event = {
        key: ' ',
        preventDefault: vi.fn(),
      } as unknown as React.KeyboardEvent

      props.onKeyDown(event)

      expect(event.preventDefault).toHaveBeenCalled()
      expect(mockOnSelect).toHaveBeenCalledWith(1)
    })

    it('should not call onSelect for other keys', () => {
      const props = getRowSelectionProps(mockItem, null, mockOnSelect)

      const event = {
        key: 'Escape',
        preventDefault: vi.fn(),
      } as unknown as React.KeyboardEvent

      props.onKeyDown(event)

      expect(event.preventDefault).not.toHaveBeenCalled()
      expect(mockOnSelect).not.toHaveBeenCalled()
    })
  })

  describe('selection state', () => {
    it('should return aria-selected true and bg when item is selected', () => {
      const props = getRowSelectionProps(mockItem, 1, mockOnSelect)

      expect(props['aria-selected']).toBe(true)
      expect(props.bg).toBe('var(--mantine-color-blue-light)')
    })

    it('should return aria-selected false and bg undefined when item is not selected', () => {
      const props = getRowSelectionProps(mockItem, 2, mockOnSelect)

      expect(props['aria-selected']).toBe(false)
      expect(props.bg).toBeUndefined()
    })

    it('should return aria-selected false when selectedId is null', () => {
      const props = getRowSelectionProps(mockItem, null, mockOnSelect)

      expect(props['aria-selected']).toBe(false)
      expect(props.bg).toBeUndefined()
    })
  })

  describe('static props', () => {
    it('should return correct static props', () => {
      const props = getRowSelectionProps(mockItem, null, mockOnSelect)

      expect(props.tabIndex).toBe(0)
      expect(props.style).toEqual({ cursor: 'pointer' })
    })
  })
})
