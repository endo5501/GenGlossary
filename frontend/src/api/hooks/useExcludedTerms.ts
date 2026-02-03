import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query'
import { apiClient } from '../client'
import type {
  ExcludedTermResponse,
  ExcludedTermListResponse,
  ExcludedTermCreateRequest,
} from '../types'
import { termKeys } from './useTerms'

export const excludedTermKeys = {
  all: ['excludedTerms'] as const,
  lists: () => [...excludedTermKeys.all, 'list'] as const,
  list: (projectId: number) => [...excludedTermKeys.lists(), projectId] as const,
}

export function useExcludedTerms(projectId: number | undefined) {
  return useQuery({
    queryKey: excludedTermKeys.list(projectId!),
    queryFn: async () => {
      const response = await apiClient.get<ExcludedTermListResponse>(
        `/api/projects/${projectId}/excluded-terms`
      )
      return response.items
    },
    enabled: projectId !== undefined,
  })
}

export function useCreateExcludedTerm(projectId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: ExcludedTermCreateRequest) =>
      apiClient.post<ExcludedTermResponse>(`/api/projects/${projectId}/excluded-terms`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: excludedTermKeys.list(projectId) })
      // Also invalidate terms list as the term might be removed from there
      queryClient.invalidateQueries({ queryKey: termKeys.list(projectId) })
    },
  })
}

export function useDeleteExcludedTerm(projectId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (termId: number) =>
      apiClient.delete<void>(`/api/projects/${projectId}/excluded-terms/${termId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: excludedTermKeys.list(projectId) })
      // Also invalidate terms list as the deleted term might reappear there
      queryClient.invalidateQueries({ queryKey: termKeys.list(projectId) })
    },
  })
}
