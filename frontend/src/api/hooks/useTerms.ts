import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../client'
import type {
  TermResponse,
  TermCreateRequest,
  TermUpdateRequest,
  RunResponse,
} from '../types'
import { useResourceList, useResourceDetail } from './useResource'
import { runKeys } from './useRuns'

export const termKeys = {
  all: ['terms'] as const,
  lists: () => [...termKeys.all, 'list'] as const,
  list: (projectId: number) => [...termKeys.lists(), projectId] as const,
  details: () => [...termKeys.all, 'detail'] as const,
  detail: (projectId: number, termId: number) =>
    [...termKeys.details(), projectId, termId] as const,
}

const termApi = {
  list: (projectId: number) =>
    apiClient.get<TermResponse[]>(`/api/projects/${projectId}/terms`),
  get: (projectId: number, termId: number) =>
    apiClient.get<TermResponse>(`/api/projects/${projectId}/terms/${termId}`),
  create: (projectId: number, data: TermCreateRequest) =>
    apiClient.post<TermResponse>(`/api/projects/${projectId}/terms`, data),
  update: (projectId: number, termId: number, data: TermUpdateRequest) =>
    apiClient.patch<TermResponse>(`/api/projects/${projectId}/terms/${termId}`, data),
  delete: (projectId: number, termId: number) =>
    apiClient.delete<void>(`/api/projects/${projectId}/terms/${termId}`),
  extract: (projectId: number) =>
    apiClient.post<RunResponse>(`/api/projects/${projectId}/runs`, { scope: 'extract' }),
}

export function useTerms(projectId: number | undefined) {
  return useResourceList({
    queryKey: termKeys.list(projectId!),
    queryFn: () => termApi.list(projectId!),
    enabled: projectId !== undefined,
  })
}

export function useTerm(projectId: number | undefined, termId: number | undefined) {
  return useResourceDetail({
    queryKey: termKeys.detail(projectId!, termId!),
    queryFn: () => termApi.get(projectId!, termId!),
    enabled: projectId !== undefined && termId !== undefined,
  })
}

export function useCreateTerm(projectId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: TermCreateRequest) => termApi.create(projectId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: termKeys.list(projectId) })
    },
  })
}

export function useUpdateTerm(projectId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ termId, data }: { termId: number; data: TermUpdateRequest }) =>
      termApi.update(projectId, termId, data),
    onSuccess: (_, { termId }) => {
      queryClient.invalidateQueries({ queryKey: termKeys.detail(projectId, termId) })
      queryClient.invalidateQueries({ queryKey: termKeys.list(projectId) })
    },
  })
}

export function useDeleteTerm(projectId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (termId: number) => termApi.delete(projectId, termId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: termKeys.list(projectId) })
    },
  })
}

export function useExtractTerms(projectId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => termApi.extract(projectId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: termKeys.list(projectId) })
      queryClient.invalidateQueries({ queryKey: runKeys.current(projectId) })
    },
  })
}
