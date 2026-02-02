import { useQuery } from '@tanstack/react-query'
import { useState, useEffect } from 'react'
import { apiClient, ApiError } from '../client'

interface OllamaModelsResponse {
  models: { name: string }[]
}

export const ollamaKeys = {
  all: ['ollama'] as const,
  models: (baseUrl: string) => [...ollamaKeys.all, 'models', baseUrl] as const,
}

const ollamaApi = {
  listModels: (baseUrl: string) =>
    apiClient.get<OllamaModelsResponse>(
      `/api/ollama/models?base_url=${encodeURIComponent(baseUrl)}`
    ),
}

export function useOllamaModels(baseUrl: string) {
  const [debouncedUrl, setDebouncedUrl] = useState(baseUrl)

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedUrl(baseUrl)
    }, 500)

    return () => clearTimeout(timer)
  }, [baseUrl])

  const query = useQuery({
    queryKey: ollamaKeys.models(debouncedUrl),
    queryFn: () => ollamaApi.listModels(debouncedUrl),
    enabled: debouncedUrl.length > 0,
    retry: false,
  })

  const models = query.data?.models.map((m) => m.name) ?? []
  const error =
    query.error instanceof ApiError ? query.error.detail ?? null : null

  return {
    models,
    isLoading: query.isLoading && debouncedUrl.length > 0,
    error,
    refetch: query.refetch,
  }
}
