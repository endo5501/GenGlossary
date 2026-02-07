import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query'
import { apiClient } from '../client'
import { termKeys } from './useTerms'

/**
 * Shared term response shape (common to excluded and required terms).
 */
interface TermListResponse<T> {
  items: T[]
  total: number
}

interface TermCreateRequest {
  term_text: string
}

interface UseTermsCrudOptions {
  /** API path segment, e.g. "excluded-terms" or "required-terms" */
  apiPath: string
  /** Query key prefix, e.g. "excludedTerms" or "requiredTerms" */
  queryKeyPrefix: string
}

function makeTermKeys(prefix: string) {
  return {
    all: [prefix] as const,
    lists: () => [...makeTermKeys(prefix).all, 'list'] as const,
    list: (projectId: number) => [...makeTermKeys(prefix).lists(), projectId] as const,
  }
}

export function useTermsList<T>(
  projectId: number | undefined,
  options: UseTermsCrudOptions,
) {
  const keys = makeTermKeys(options.queryKeyPrefix)

  return {
    ...useQuery({
      queryKey: keys.list(projectId!),
      queryFn: async () => {
        const response = await apiClient.get<TermListResponse<T>>(
          `/api/projects/${projectId}/${options.apiPath}`
        )
        return response.items
      },
      enabled: projectId !== undefined,
    }),
    keys,
  }
}

export function useCreateTerm<T>(
  projectId: number,
  options: UseTermsCrudOptions,
) {
  const queryClient = useQueryClient()
  const keys = makeTermKeys(options.queryKeyPrefix)

  return useMutation({
    mutationFn: (data: TermCreateRequest) =>
      apiClient.post<T>(`/api/projects/${projectId}/${options.apiPath}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: keys.list(projectId) })
      queryClient.invalidateQueries({ queryKey: termKeys.list(projectId) })
    },
  })
}

export function useDeleteTerm(
  projectId: number,
  options: UseTermsCrudOptions,
) {
  const queryClient = useQueryClient()
  const keys = makeTermKeys(options.queryKeyPrefix)

  return useMutation({
    mutationFn: (termId: number) =>
      apiClient.delete<void>(`/api/projects/${projectId}/${options.apiPath}/${termId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: keys.list(projectId) })
      queryClient.invalidateQueries({ queryKey: termKeys.list(projectId) })
    },
  })
}
