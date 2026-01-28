import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../client'
import type { FileResponse, FileCreateRequest, FileCreateBulkRequest } from '../types'

// Query keys
export const fileKeys = {
  all: ['files'] as const,
  lists: () => [...fileKeys.all, 'list'] as const,
  list: (projectId: number) => [...fileKeys.lists(), projectId] as const,
  details: () => [...fileKeys.all, 'detail'] as const,
  detail: (projectId: number, fileId: number) =>
    [...fileKeys.details(), projectId, fileId] as const,
}

// API functions
const fileApi = {
  list: (projectId: number) =>
    apiClient.get<FileResponse[]>(`/api/projects/${projectId}/files`),
  get: (projectId: number, fileId: number) =>
    apiClient.get<FileResponse>(`/api/projects/${projectId}/files/${fileId}`),
  create: (projectId: number, data: FileCreateRequest) =>
    apiClient.post<FileResponse>(`/api/projects/${projectId}/files`, data),
  createBulk: (projectId: number, data: FileCreateBulkRequest) =>
    apiClient.post<FileResponse[]>(`/api/projects/${projectId}/files/bulk`, data),
  delete: (projectId: number, fileId: number) =>
    apiClient.delete<void>(`/api/projects/${projectId}/files/${fileId}`),
}

// Hooks
export function useFiles(projectId: number | undefined) {
  return useQuery({
    queryKey: fileKeys.list(projectId!),
    queryFn: () => fileApi.list(projectId!),
    enabled: projectId !== undefined,
  })
}

export function useFile(projectId: number | undefined, fileId: number | undefined) {
  return useQuery({
    queryKey: fileKeys.detail(projectId!, fileId!),
    queryFn: () => fileApi.get(projectId!, fileId!),
    enabled: projectId !== undefined && fileId !== undefined,
  })
}

export function useCreateFile(projectId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: FileCreateRequest) => fileApi.create(projectId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: fileKeys.list(projectId) })
    },
  })
}

export function useCreateFilesBulk(projectId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (files: FileCreateRequest[]) =>
      fileApi.createBulk(projectId, { files }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: fileKeys.list(projectId) })
    },
  })
}

export function useDeleteFile(projectId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (fileId: number) => fileApi.delete(projectId, fileId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: fileKeys.list(projectId) })
    },
  })
}
