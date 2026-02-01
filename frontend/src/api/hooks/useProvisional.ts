import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../client'
import type { GlossaryTermResponse, ProvisionalUpdateRequest, RunResponse } from '../types'
import { useResourceList, useResourceDetail } from './useResource'
import { runKeys } from './useRuns'

export const provisionalKeys = {
  all: ['provisional'] as const,
  lists: () => [...provisionalKeys.all, 'list'] as const,
  list: (projectId: number) => [...provisionalKeys.lists(), projectId] as const,
  details: () => [...provisionalKeys.all, 'detail'] as const,
  detail: (projectId: number, entryId: number) =>
    [...provisionalKeys.details(), projectId, entryId] as const,
}

const provisionalApi = {
  list: (projectId: number) =>
    apiClient.get<GlossaryTermResponse[]>(`/api/projects/${projectId}/provisional`),
  get: (projectId: number, entryId: number) =>
    apiClient.get<GlossaryTermResponse>(`/api/projects/${projectId}/provisional/${entryId}`),
  update: (projectId: number, entryId: number, data: ProvisionalUpdateRequest) =>
    apiClient.patch<GlossaryTermResponse>(
      `/api/projects/${projectId}/provisional/${entryId}`,
      data
    ),
  regenerate: (projectId: number) =>
    apiClient.post<RunResponse>(`/api/projects/${projectId}/runs`, { scope: 'generate' }),
}

export function useProvisional(projectId: number | undefined) {
  return useResourceList({
    queryKey: provisionalKeys.list(projectId!),
    queryFn: () => provisionalApi.list(projectId!),
    enabled: projectId !== undefined,
  })
}

export function useProvisionalEntry(
  projectId: number | undefined,
  entryId: number | undefined
) {
  return useResourceDetail({
    queryKey: provisionalKeys.detail(projectId!, entryId!),
    queryFn: () => provisionalApi.get(projectId!, entryId!),
    enabled: projectId !== undefined && entryId !== undefined,
  })
}

export function useUpdateProvisional(projectId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ entryId, data }: { entryId: number; data: ProvisionalUpdateRequest }) =>
      provisionalApi.update(projectId, entryId, data),
    onSuccess: (_, { entryId }) => {
      queryClient.invalidateQueries({
        queryKey: provisionalKeys.detail(projectId, entryId),
      })
      queryClient.invalidateQueries({ queryKey: provisionalKeys.list(projectId) })
    },
  })
}

export function useRegenerateProvisional(projectId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => provisionalApi.regenerate(projectId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: provisionalKeys.list(projectId) })
      queryClient.invalidateQueries({ queryKey: runKeys.current(projectId) })
    },
  })
}
