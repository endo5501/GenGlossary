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
    vi.useFakeTimers({ shouldAdvanceTime: true })
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
    act(() => {
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

    act(() => {
      vi.advanceTimersByTime(500)
    })

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.models).toEqual(['codellama'])
  })

  it('should update models when base URL changes', async () => {
    let lastRequestUrl = ''

    server.use(
      http.get('http://localhost:8000/api/ollama/models', ({ request }) => {
        lastRequestUrl = new URL(request.url).searchParams.get('base_url') || ''
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

    act(() => {
      vi.advanceTimersByTime(500)
    })

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    // Change URL
    rerender({ baseUrl: 'http://localhost:11436' })

    act(() => {
      vi.advanceTimersByTime(500)
    })

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    // Final request should use the new URL
    expect(lastRequestUrl).toBe('http://localhost:11436')
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

    act(() => {
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

    act(() => {
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

    act(() => {
      vi.advanceTimersByTime(500)
    })

    expect(requestCount).toBe(0)
    expect(result.current.models).toEqual([])
    expect(result.current.isLoading).toBe(false)
  })
})
