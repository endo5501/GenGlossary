import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../client'
import type {
  SynonymGroupResponse,
  SynonymGroupListResponse,
  SynonymGroupCreateRequest,
  SynonymGroupUpdateRequest,
  SynonymMemberCreateRequest,
  SynonymMemberResponse,
} from '../types'

export const synonymGroupKeys = {
  all: ['synonymGroups'] as const,
  lists: () => [...synonymGroupKeys.all, 'list'] as const,
  list: (projectId: number) => [...synonymGroupKeys.lists(), projectId] as const,
}

export function useSynonymGroups(projectId: number | undefined) {
  return useQuery({
    queryKey: synonymGroupKeys.list(projectId!),
    queryFn: async () => {
      const response = await apiClient.get<SynonymGroupListResponse>(
        `/api/projects/${projectId}/synonym-groups`
      )
      return response.items
    },
    enabled: projectId !== undefined,
  })
}

export function useCreateSynonymGroup(projectId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: SynonymGroupCreateRequest) =>
      apiClient.post<SynonymGroupResponse>(
        `/api/projects/${projectId}/synonym-groups`,
        data
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: synonymGroupKeys.list(projectId) })
    },
  })
}

export function useDeleteSynonymGroup(projectId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (groupId: number) =>
      apiClient.delete<void>(
        `/api/projects/${projectId}/synonym-groups/${groupId}`
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: synonymGroupKeys.list(projectId) })
    },
  })
}

export function useUpdateSynonymGroup(projectId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ groupId, data }: { groupId: number; data: SynonymGroupUpdateRequest }) =>
      apiClient.patch<SynonymGroupResponse>(
        `/api/projects/${projectId}/synonym-groups/${groupId}`,
        data
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: synonymGroupKeys.list(projectId) })
    },
  })
}

export function useAddSynonymMember(projectId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ groupId, data }: { groupId: number; data: SynonymMemberCreateRequest }) =>
      apiClient.post<SynonymMemberResponse>(
        `/api/projects/${projectId}/synonym-groups/${groupId}/members`,
        data
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: synonymGroupKeys.list(projectId) })
    },
  })
}

export function useRemoveSynonymMember(projectId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ groupId, memberId }: { groupId: number; memberId: number }) =>
      apiClient.delete<void>(
        `/api/projects/${projectId}/synonym-groups/${groupId}/members/${memberId}`
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: synonymGroupKeys.list(projectId) })
    },
  })
}
