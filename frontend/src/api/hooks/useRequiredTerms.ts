import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query'
import { apiClient } from '../client'
import type {
  RequiredTermResponse,
  RequiredTermListResponse,
  RequiredTermCreateRequest,
} from '../types'
import { termKeys } from './useTerms'

export const requiredTermKeys = {
  all: ['requiredTerms'] as const,
  lists: () => [...requiredTermKeys.all, 'list'] as const,
  list: (projectId: number) => [...requiredTermKeys.lists(), projectId] as const,
}

export function useRequiredTerms(projectId: number | undefined) {
  return useQuery({
    queryKey: requiredTermKeys.list(projectId!),
    queryFn: async () => {
      const response = await apiClient.get<RequiredTermListResponse>(
        `/api/projects/${projectId}/required-terms`
      )
      return response.items
    },
    enabled: projectId !== undefined,
  })
}

export function useCreateRequiredTerm(projectId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: RequiredTermCreateRequest) =>
      apiClient.post<RequiredTermResponse>(`/api/projects/${projectId}/required-terms`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: requiredTermKeys.list(projectId) })
      queryClient.invalidateQueries({ queryKey: termKeys.list(projectId) })
    },
  })
}

export function useDeleteRequiredTerm(projectId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (termId: number) =>
      apiClient.delete<void>(`/api/projects/${projectId}/required-terms/${termId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: requiredTermKeys.list(projectId) })
      queryClient.invalidateQueries({ queryKey: termKeys.list(projectId) })
    },
  })
}
