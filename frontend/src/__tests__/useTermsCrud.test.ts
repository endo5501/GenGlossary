import { describe, expect, it } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { http, HttpResponse } from 'msw'
import { server } from './setup'
import { useTermsList } from '../api/hooks/useTermsCrud'
import React from 'react'

const BASE_URL = 'http://localhost:8000'

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

const OPTIONS = {
  apiPath: 'excluded-terms',
  queryKeyPrefix: 'excludedTerms',
} as const

describe('useTermsList', () => {
  it('does not fetch when projectId is undefined', async () => {
    let requestCount = 0

    server.use(
      http.get(`${BASE_URL}/api/projects/:projectId/excluded-terms`, () => {
        requestCount++
        return HttpResponse.json({ items: [], total: 0 })
      })
    )

    const { result } = renderHook(
      () => useTermsList(undefined, OPTIONS),
      { wrapper: createWrapper() }
    )

    // Wait a bit to ensure no request is made
    await new Promise(resolve => setTimeout(resolve, 100))

    expect(requestCount).toBe(0)
    expect(result.current.data).toBeUndefined()
    expect(result.current.isFetching).toBe(false)
  })

  it('fetches when projectId is defined', async () => {
    server.use(
      http.get(`${BASE_URL}/api/projects/:projectId/excluded-terms`, () => {
        return HttpResponse.json({
          items: [{ id: 1, term_text: 'test', source: 'auto', created_at: '2024-01-01T00:00:00Z' }],
          total: 1,
        })
      })
    )

    const { result } = renderHook(
      () => useTermsList(1, OPTIONS),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.data).toHaveLength(1)
    expect(result.current.data?.[0]).toMatchObject({ id: 1, term_text: 'test' })
  })
})
