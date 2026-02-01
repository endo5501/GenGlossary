import { describe, it, expect, beforeEach, vi } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useLogStream } from '../api/hooks/useLogStream'
import { useLogStore } from '../store/logStore'

// Get the mocked EventSource from setup.ts
const MockedEventSource = window.EventSource as unknown as {
  new (url: string): {
    url: string
    readyState: number
    onopen: ((event: Event) => void) | null
    onmessage: ((event: MessageEvent) => void) | null
    onerror: ((event: Event) => void) | null
    addEventListener: ReturnType<typeof vi.fn>
    removeEventListener: ReturnType<typeof vi.fn>
    close: ReturnType<typeof vi.fn>
  }
  CONNECTING: 0
  OPEN: 1
  CLOSED: 2
}

describe('useLogStream', () => {
  beforeEach(() => {
    // Reset store before each test
    useLogStore.getState().clearLogs()
    useLogStore.getState().setCurrentContext(null, null)
    vi.clearAllMocks()
  })

  describe('runId = 0 handling', () => {
    it('should connect when runId is 0 (not treat 0 as falsy)', async () => {
      // BUG: Currently `if (!runId)` treats runId=0 as "no run"
      // FIX: Should use `runId === undefined` or `runId == null`
      const { result } = renderHook(() => useLogStream(1, 0))

      // Wait for connection to establish
      await waitFor(() => {
        expect(result.current.isConnected).toBe(true)
      })

      // runId=0 should be treated as a valid run and connect
      expect(result.current.isConnected).toBe(true)
    })

    it('should not connect when runId is undefined', () => {
      const { result } = renderHook(() => useLogStream(1, undefined))

      // undefined should not connect
      expect(result.current.isConnected).toBe(false)
    })
  })

  describe('error state clearing', () => {
    it('should clear error state when runId becomes undefined', async () => {
      let eventSourceInstance: InstanceType<typeof MockedEventSource> | null =
        null

      // Capture the EventSource instance
      const OriginalEventSource = window.EventSource
      window.EventSource = class extends (
        OriginalEventSource
      ) {
        constructor(url: string) {
          super(url)
          eventSourceInstance = this as unknown as InstanceType<
            typeof MockedEventSource
          >
        }
      } as typeof EventSource

      try {
        const { result, rerender } = renderHook(
          ({ runId }) => useLogStream(1, runId),
          { initialProps: { runId: 1 as number | undefined } }
        )

        // Wait for connection
        await waitFor(() => {
          expect(eventSourceInstance).not.toBeNull()
        })

        // Simulate SSE error
        act(() => {
          eventSourceInstance!.onerror?.(new Event('error'))
        })

        // Verify error is set
        expect(result.current.error).not.toBeNull()
        expect(result.current.error?.message).toBe('SSE connection error')

        // Change runId to undefined (no active run)
        rerender({ runId: undefined })

        // Error should be cleared when runId becomes undefined
        // Use waitFor because setError(null) happens in useEffect after render
        await waitFor(() => {
          expect(result.current.error).toBeNull()
        })
      } finally {
        window.EventSource = OriginalEventSource
      }
    })
  })

  describe('onComplete stale closure', () => {
    it('should call the latest onComplete callback when complete event fires', async () => {
      const onComplete1 = vi.fn()
      const onComplete2 = vi.fn()

      let eventSourceInstance: InstanceType<typeof MockedEventSource> | null =
        null

      // Capture the EventSource instance
      const OriginalEventSource = window.EventSource
      window.EventSource = class extends (
        OriginalEventSource
      ) {
        constructor(url: string) {
          super(url)
          eventSourceInstance = this as unknown as InstanceType<
            typeof MockedEventSource
          >
        }
      } as typeof EventSource

      try {
        const { rerender } = renderHook(
          ({ onComplete }) => useLogStream(1, 1, { onComplete }),
          { initialProps: { onComplete: onComplete1 } }
        )

        // Wait for connection
        await waitFor(() => {
          expect(eventSourceInstance).not.toBeNull()
        })

        // Update callback (simulating prop change)
        rerender({ onComplete: onComplete2 })

        // Trigger complete event
        act(() => {
          // Find the 'complete' event listener
          const addEventListenerCalls =
            eventSourceInstance!.addEventListener.mock.calls
          const completeHandler = addEventListenerCalls.find(
            (call: [string, unknown]) => call[0] === 'complete'
          )?.[1] as (() => void) | undefined

          if (completeHandler) {
            completeHandler()
          }
        })

        // BUG: Currently onComplete1 is called because it's captured in closure
        // FIX: onComplete should be in dependency array so latest callback is used
        expect(onComplete1).not.toHaveBeenCalled()
        expect(onComplete2).toHaveBeenCalledTimes(1)
      } finally {
        window.EventSource = OriginalEventSource
      }
    })
  })
})
