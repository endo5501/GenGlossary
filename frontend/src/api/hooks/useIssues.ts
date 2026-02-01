import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../client'
import type { IssueResponse, IssueType, RunResponse } from '../types'
import { useResourceList, useResourceDetail } from './useResource'
import { runKeys } from './useRuns'

export const issueKeys = {
  all: ['issues'] as const,
  lists: () => [...issueKeys.all, 'list'] as const,
  list: (projectId: number, issueType?: IssueType) =>
    issueType
      ? [...issueKeys.lists(), projectId, issueType] as const
      : [...issueKeys.lists(), projectId] as const,
  details: () => [...issueKeys.all, 'detail'] as const,
  detail: (projectId: number, issueId: number) =>
    [...issueKeys.details(), projectId, issueId] as const,
}

const issueApi = {
  list: (projectId: number, issueType?: IssueType) => {
    const url = issueType
      ? `/api/projects/${projectId}/issues?issue_type=${issueType}`
      : `/api/projects/${projectId}/issues`
    return apiClient.get<IssueResponse[]>(url)
  },
  get: (projectId: number, issueId: number) =>
    apiClient.get<IssueResponse>(`/api/projects/${projectId}/issues/${issueId}`),
  review: (projectId: number) =>
    apiClient.post<RunResponse>(`/api/projects/${projectId}/runs`, { scope: 'review' }),
}

export function useIssues(projectId: number | undefined, issueType?: IssueType) {
  return useResourceList({
    queryKey: issueKeys.list(projectId!, issueType),
    queryFn: () => issueApi.list(projectId!, issueType),
    enabled: projectId !== undefined,
  })
}

export function useIssue(projectId: number | undefined, issueId: number | undefined) {
  return useResourceDetail({
    queryKey: issueKeys.detail(projectId!, issueId!),
    queryFn: () => issueApi.get(projectId!, issueId!),
    enabled: projectId !== undefined && issueId !== undefined,
  })
}

export function useReviewIssues(projectId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => issueApi.review(projectId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: issueKeys.lists() })
      queryClient.invalidateQueries({ queryKey: runKeys.current(projectId) })
    },
  })
}
