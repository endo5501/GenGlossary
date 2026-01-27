import '@testing-library/jest-dom'
import { setupServer } from 'msw/node'
import { afterAll, afterEach, beforeAll, vi } from 'vitest'

// Mock window.matchMedia for Mantine
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// Mock ResizeObserver
class ResizeObserverMock {
  observe = vi.fn()
  unobserve = vi.fn()
  disconnect = vi.fn()
}

Object.defineProperty(window, 'ResizeObserver', {
  writable: true,
  value: ResizeObserverMock,
})

// Mock scrollIntoView for Mantine Combobox
Element.prototype.scrollIntoView = vi.fn()

// Mock EventSource for SSE tests
class EventSourceMock {
  static CONNECTING = 0 as const
  static OPEN = 1 as const
  static CLOSED = 2 as const

  url: string
  readyState = EventSourceMock.CONNECTING
  onopen: ((event: Event) => void) | null = null
  onmessage: ((event: MessageEvent) => void) | null = null
  onerror: ((event: Event) => void) | null = null

  addEventListener = vi.fn()
  removeEventListener = vi.fn()
  close = vi.fn(() => {
    this.readyState = EventSourceMock.CLOSED
  })

  constructor(url: string) {
    this.url = url
    // Simulate immediate connection for simpler tests
    queueMicrotask(() => {
      this.readyState = EventSourceMock.OPEN
      this.onopen?.(new Event('open'))
    })
  }
}

Object.defineProperty(window, 'EventSource', {
  writable: true,
  value: EventSourceMock,
})

// MSW server setup for API mocking
export const server = setupServer()

beforeAll(() => {
  server.listen({ onUnhandledRequest: 'bypass' })
})

afterEach(() => {
  server.resetHandlers()
})

afterAll(() => {
  server.close()
})
