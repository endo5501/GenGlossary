import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient, getBaseUrl } from '../client'
import type { GlossaryTermResponse } from '../types'
import { useResourceList, useResourceDetail } from './useResource'

export const refinedKeys = {
  all: ['refined'] as const,
  lists: () => [...refinedKeys.all, 'list'] as const,
  list: (projectId: number) => [...refinedKeys.lists(), projectId] as const,
  details: () => [...refinedKeys.all, 'detail'] as const,
  detail: (projectId: number, termId: number) =>
    [...refinedKeys.details(), projectId, termId] as const,
}

const refinedApi = {
  list: (projectId: number) =>
    apiClient.get<GlossaryTermResponse[]>(`/api/projects/${projectId}/refined`),
  get: (projectId: number, termId: number) =>
    apiClient.get<GlossaryTermResponse>(`/api/projects/${projectId}/refined/${termId}`),
  exportMarkdown: async (projectId: number) => {
    const response = await fetch(
      `${getBaseUrl()}/api/projects/${projectId}/refined/export`
    )
    if (!response.ok) {
      throw new Error('Export failed')
    }
    return response.text()
  },
  regenerate: (projectId: number) =>
    apiClient.post<{ message: string }>(`/api/projects/${projectId}/refined/regenerate`, {}),
}

export function useRefined(projectId: number | undefined) {
  return useResourceList({
    queryKey: refinedKeys.list(projectId!),
    queryFn: () => refinedApi.list(projectId!),
    enabled: projectId !== undefined,
  })
}

export function useRefinedEntry(
  projectId: number | undefined,
  termId: number | undefined
) {
  return useResourceDetail({
    queryKey: refinedKeys.detail(projectId!, termId!),
    queryFn: () => refinedApi.get(projectId!, termId!),
    enabled: projectId !== undefined && termId !== undefined,
  })
}

export function useExportMarkdown(projectId: number) {
  return useMutation({
    mutationFn: () => refinedApi.exportMarkdown(projectId),
    onSuccess: (markdown) => {
      // Create download
      const blob = new Blob([markdown], { type: 'text/markdown' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'glossary.md'
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    },
  })
}

export function useRegenerateRefined(projectId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => refinedApi.regenerate(projectId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: refinedKeys.list(projectId) })
    },
  })
}
