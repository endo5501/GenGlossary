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

const excludedTermApi = {
  list: (projectId: number) =>
    apiClient.get<ExcludedTermListResponse>(`/api/projects/${projectId}/excluded-terms`),
  create: (projectId: number, data: ExcludedTermCreateRequest) =>
    apiClient.post<ExcludedTermResponse>(`/api/projects/${projectId}/excluded-terms`, data),
  delete: (projectId: number, termId: number) =>
    apiClient.delete<void>(`/api/projects/${projectId}/excluded-terms/${termId}`),
}

export function useExcludedTerms(projectId: number | undefined) {
  return useQuery({
    queryKey: excludedTermKeys.list(projectId!),
    queryFn: async () => {
      const response = await excludedTermApi.list(projectId!)
      return response.items
    },
    enabled: projectId !== undefined,
  })
}

export function useCreateExcludedTerm(projectId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: ExcludedTermCreateRequest) => excludedTermApi.create(projectId, data),
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
    mutationFn: (termId: number) => excludedTermApi.delete(projectId, termId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: excludedTermKeys.list(projectId) })
      // Also invalidate terms list as the deleted term might reappear there
      queryClient.invalidateQueries({ queryKey: termKeys.list(projectId) })
    },
  })
}
