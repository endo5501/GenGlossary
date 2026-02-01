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
  private listeners: Map<string, Set<EventListener>> = new Map()

  addEventListener = vi.fn((event: string, handler: EventListener) => {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set())
    }
    this.listeners.get(event)!.add(handler)
  })

  removeEventListener = vi.fn((event: string, handler: EventListener) => {
    this.listeners.get(event)?.delete(handler)
  })

  close = vi.fn(() => {
    this.readyState = EventSourceMock.CLOSED
    this.listeners.clear()
  })

  // Helper to dispatch events to registered listeners
  dispatchEvent(event: Event) {
    this.listeners.get(event.type)?.forEach((handler) => handler(event))
    return true
  }

  constructor(url: string) {
    this.url = url
    // Simulate immediate connection for simpler tests
    queueMicrotask(() => {
      this.readyState = EventSourceMock.OPEN
      this.dispatchEvent(new Event('open'))
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
