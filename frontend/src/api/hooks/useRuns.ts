import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../client'
import type { RunResponse, RunCreateRequest } from '../types'

export const runKeys = {
  all: ['runs'] as const,
  current: (projectId: number) => [...runKeys.all, 'current', projectId] as const,
}

const runApi = {
  getCurrent: (projectId: number) =>
    apiClient.get<RunResponse>(`/api/projects/${projectId}/runs/current`),
  start: (projectId: number, data: RunCreateRequest) =>
    apiClient.post<RunResponse>(`/api/projects/${projectId}/runs`, data),
  cancel: (projectId: number, runId: number) =>
    apiClient.post<RunResponse>(`/api/projects/${projectId}/runs/${runId}/cancel`, {}),
}

export function useCurrentRun(projectId: number | undefined) {
  return useQuery({
    queryKey: runKeys.current(projectId!),
    queryFn: () => runApi.getCurrent(projectId!),
    enabled: projectId !== undefined,
    refetchInterval: (query) =>
      query.state.data?.status === 'running' ? 2000 : false,
  })
}

export function useStartRun(projectId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: RunCreateRequest) => runApi.start(projectId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: runKeys.current(projectId) })
    },
  })
}

export function useCancelRun(projectId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (runId: number) => runApi.cancel(projectId, runId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: runKeys.current(projectId) })
    },
  })
}
