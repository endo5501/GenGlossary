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

  // Trim whitespace and check if URL is valid
  const trimmedUrl = debouncedUrl.trim()
  const isValidUrl = trimmedUrl.length > 0

  const query = useQuery({
    queryKey: ollamaKeys.models(trimmedUrl),
    queryFn: () => ollamaApi.listModels(trimmedUrl),
    enabled: isValidUrl,
    retry: false,
  })

  const models = query.data?.models.map((m) => m.name) ?? []

  // Handle both ApiError and other errors
  let error: string | null = null
  if (query.error) {
    if (query.error instanceof ApiError) {
      error = query.error.detail ?? 'Failed to fetch models'
    } else if (query.error instanceof Error) {
      error = query.error.message
    } else {
      error = 'Failed to fetch models'
    }
  }

  return {
    models,
    isLoading: query.isLoading && isValidUrl,
    error,
    refetch: query.refetch,
  }
}
