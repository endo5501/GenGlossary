import { describe, expect, it, vi } from 'vitest'
import { renderHook } from '@testing-library/react'
import { useRowSelection } from '../hooks/useRowSelection'

describe('useRowSelection', () => {
  const mockItem = { id: 1, name: 'Test Item' }
  const mockOnSelect = vi.fn()

  beforeEach(() => {
    mockOnSelect.mockClear()
  })

  describe('onClick', () => {
    it('should call onSelect with item id when clicked', () => {
      const { result } = renderHook(() =>
        useRowSelection(mockItem, null, mockOnSelect)
      )

      result.current.onClick()

      expect(mockOnSelect).toHaveBeenCalledWith(1)
      expect(mockOnSelect).toHaveBeenCalledTimes(1)
    })
  })

  describe('onKeyDown', () => {
    it('should call onSelect when Enter key is pressed', () => {
      const { result } = renderHook(() =>
        useRowSelection(mockItem, null, mockOnSelect)
      )

      const event = {
        key: 'Enter',
        preventDefault: vi.fn(),
      } as unknown as React.KeyboardEvent

      result.current.onKeyDown(event)

      expect(event.preventDefault).toHaveBeenCalled()
      expect(mockOnSelect).toHaveBeenCalledWith(1)
    })

    it('should call onSelect when Space key is pressed', () => {
      const { result } = renderHook(() =>
        useRowSelection(mockItem, null, mockOnSelect)
      )

      const event = {
        key: ' ',
        preventDefault: vi.fn(),
      } as unknown as React.KeyboardEvent

      result.current.onKeyDown(event)

      expect(event.preventDefault).toHaveBeenCalled()
      expect(mockOnSelect).toHaveBeenCalledWith(1)
    })

    it('should not call onSelect for other keys', () => {
      const { result } = renderHook(() =>
        useRowSelection(mockItem, null, mockOnSelect)
      )

      const event = {
        key: 'Escape',
        preventDefault: vi.fn(),
      } as unknown as React.KeyboardEvent

      result.current.onKeyDown(event)

      expect(event.preventDefault).not.toHaveBeenCalled()
      expect(mockOnSelect).not.toHaveBeenCalled()
    })
  })

  describe('selection state', () => {
    it('should return aria-selected true and bg when item is selected', () => {
      const { result } = renderHook(() =>
        useRowSelection(mockItem, 1, mockOnSelect)
      )

      expect(result.current['aria-selected']).toBe(true)
      expect(result.current.bg).toBe('var(--mantine-color-blue-light)')
    })

    it('should return aria-selected false and bg undefined when item is not selected', () => {
      const { result } = renderHook(() =>
        useRowSelection(mockItem, 2, mockOnSelect)
      )

      expect(result.current['aria-selected']).toBe(false)
      expect(result.current.bg).toBeUndefined()
    })

    it('should return aria-selected false when selectedId is null', () => {
      const { result } = renderHook(() =>
        useRowSelection(mockItem, null, mockOnSelect)
      )

      expect(result.current['aria-selected']).toBe(false)
      expect(result.current.bg).toBeUndefined()
    })
  })

  describe('static props', () => {
    it('should return correct static props', () => {
      const { result } = renderHook(() =>
        useRowSelection(mockItem, null, mockOnSelect)
      )

      expect(result.current.tabIndex).toBe(0)
      expect(result.current.role).toBe('button')
      expect(result.current.style).toEqual({ cursor: 'pointer' })
    })
  })
})
