import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../client'
import type {
  ProjectResponse,
  ProjectCreateRequest,
  ProjectCloneRequest,
  ProjectUpdateRequest,
} from '../types'

// Query keys
export const projectKeys = {
  all: ['projects'] as const,
  lists: () => [...projectKeys.all, 'list'] as const,
  list: () => [...projectKeys.lists()] as const,
  details: () => [...projectKeys.all, 'detail'] as const,
  detail: (id: number) => [...projectKeys.details(), id] as const,
}

// API functions
const projectApi = {
  list: () => apiClient.get<ProjectResponse[]>('/api/projects'),
  get: (id: number) => apiClient.get<ProjectResponse>(`/api/projects/${id}`),
  create: (data: ProjectCreateRequest) =>
    apiClient.post<ProjectResponse>('/api/projects', data),
  clone: (id: number, data: ProjectCloneRequest) =>
    apiClient.post<ProjectResponse>(`/api/projects/${id}/clone`, data),
  update: (id: number, data: ProjectUpdateRequest) =>
    apiClient.patch<ProjectResponse>(`/api/projects/${id}`, data),
  delete: (id: number) => apiClient.delete<void>(`/api/projects/${id}`),
}

// Hooks
export function useProjects() {
  return useQuery({
    queryKey: projectKeys.list(),
    queryFn: projectApi.list,
  })
}

export function useProject(id: number | undefined) {
  return useQuery({
    queryKey: projectKeys.detail(id!),
    queryFn: () => projectApi.get(id!),
    enabled: id !== undefined,
  })
}

export function useCreateProject() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: projectApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: projectKeys.lists() })
    },
  })
}

export function useCloneProject() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: ProjectCloneRequest }) =>
      projectApi.clone(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: projectKeys.lists() })
    },
  })
}

export function useUpdateProject() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: ProjectUpdateRequest }) =>
      projectApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: projectKeys.detail(id) })
      queryClient.invalidateQueries({ queryKey: projectKeys.lists() })
    },
  })
}

export function useDeleteProject() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: projectApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: projectKeys.lists() })
    },
  })
}
