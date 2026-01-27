import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../client'
import type { RunResponse, RunCreateRequest } from '../types'

// Query keys
export const runKeys = {
  all: ['runs'] as const,
  current: (projectId: number) => [...runKeys.all, 'current', projectId] as const,
}

// API functions
const runApi = {
  getCurrent: (projectId: number) =>
    apiClient.get<RunResponse>(`/api/projects/${projectId}/runs/current`),
  start: (projectId: number, data: RunCreateRequest) =>
    apiClient.post<RunResponse>(`/api/projects/${projectId}/runs`, data),
  cancel: (projectId: number, runId: number) =>
    apiClient.post<RunResponse>(`/api/projects/${projectId}/runs/${runId}/cancel`, {}),
}

// Hooks
export function useCurrentRun(projectId: number | undefined) {
  return useQuery({
    queryKey: runKeys.current(projectId!),
    queryFn: () => runApi.getCurrent(projectId!),
    enabled: projectId !== undefined,
    refetchInterval: (query) => {
      // Poll every 2 seconds while running
      const data = query.state.data
      if (data && data.status === 'running') {
        return 2000
      }
      return false
    },
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
