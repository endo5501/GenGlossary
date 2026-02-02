import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, waitFor, act } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { http, HttpResponse } from 'msw'
import { server } from './setup'
import { useOllamaModels } from '../api/hooks/useOllamaModels'
import React from 'react'

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(
      QueryClientProvider,
      { client: queryClient },
      children
    )
  }
}

describe('useOllamaModels', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('should fetch models from default base URL', async () => {
    server.use(
      http.get('http://localhost:8000/api/ollama/models', () => {
        return HttpResponse.json({
          models: [{ name: 'llama2' }, { name: 'llama3.2' }],
        })
      })
    )

    const { result } = renderHook(
      () => useOllamaModels('http://localhost:11434'),
      { wrapper: createWrapper() }
    )

    // Wait for debounce
    await act(async () => {
      vi.advanceTimersByTime(500)
    })

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.models).toEqual(['llama2', 'llama3.2'])
    expect(result.current.error).toBeNull()
  })

  it('should fetch models with custom base URL', async () => {
    server.use(
      http.get('http://localhost:8000/api/ollama/models', ({ request }) => {
        const url = new URL(request.url)
        expect(url.searchParams.get('base_url')).toBe('http://remote:11434')
        return HttpResponse.json({
          models: [{ name: 'codellama' }],
        })
      })
    )

    const { result } = renderHook(() => useOllamaModels('http://remote:11434'), {
      wrapper: createWrapper(),
    })

    await act(async () => {
      vi.advanceTimersByTime(500)
    })

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.models).toEqual(['codellama'])
  })

  it('should debounce requests when base URL changes rapidly', async () => {
    let requestCount = 0

    server.use(
      http.get('http://localhost:8000/api/ollama/models', () => {
        requestCount++
        return HttpResponse.json({
          models: [{ name: 'llama2' }],
        })
      })
    )

    const { result, rerender } = renderHook(
      ({ baseUrl }) => useOllamaModels(baseUrl),
      {
        wrapper: createWrapper(),
        initialProps: { baseUrl: 'http://localhost:11434' },
      }
    )

    // Rapid changes before debounce timeout
    await act(async () => {
      vi.advanceTimersByTime(100)
    })
    rerender({ baseUrl: 'http://localhost:11435' })

    await act(async () => {
      vi.advanceTimersByTime(100)
    })
    rerender({ baseUrl: 'http://localhost:11436' })

    // Wait for debounce
    await act(async () => {
      vi.advanceTimersByTime(500)
    })

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    // Should only make one request with final URL
    expect(requestCount).toBe(1)
  })

  it('should return error message on connection failure', async () => {
    server.use(
      http.get('http://localhost:8000/api/ollama/models', () => {
        return HttpResponse.json(
          { detail: 'Failed to connect to Ollama server' },
          { status: 503 }
        )
      })
    )

    const { result } = renderHook(
      () => useOllamaModels('http://localhost:11434'),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      vi.advanceTimersByTime(500)
    })

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.models).toEqual([])
    expect(result.current.error).toBe('Failed to connect to Ollama server')
  })

  it('should return error message on timeout', async () => {
    server.use(
      http.get('http://localhost:8000/api/ollama/models', () => {
        return HttpResponse.json(
          { detail: 'Ollama server timeout' },
          { status: 504 }
        )
      })
    )

    const { result } = renderHook(
      () => useOllamaModels('http://localhost:11434'),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      vi.advanceTimersByTime(500)
    })

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.models).toEqual([])
    expect(result.current.error).toBe('Ollama server timeout')
  })

  it('should not fetch when base URL is empty', async () => {
    let requestCount = 0

    server.use(
      http.get('http://localhost:8000/api/ollama/models', () => {
        requestCount++
        return HttpResponse.json({ models: [] })
      })
    )

    const { result } = renderHook(() => useOllamaModels(''), {
      wrapper: createWrapper(),
    })

    await act(async () => {
      vi.advanceTimersByTime(500)
    })

    expect(requestCount).toBe(0)
    expect(result.current.models).toEqual([])
    expect(result.current.isLoading).toBe(false)
  })
})
