import type { ExcludedTermResponse } from '../types'
import { useTermsList, useCreateTerm, useDeleteTerm } from './useTermsCrud'

const OPTIONS = {
  apiPath: 'excluded-terms',
  queryKeyPrefix: 'excludedTerms',
} as const

export const excludedTermKeys = {
  all: ['excludedTerms'] as const,
  lists: () => [...excludedTermKeys.all, 'list'] as const,
  list: (projectId: number) => [...excludedTermKeys.lists(), projectId] as const,
}

export function useExcludedTerms(projectId: number | undefined) {
  const { keys: _keys, ...result } = useTermsList<ExcludedTermResponse>(projectId, OPTIONS)
  return result
}

export function useCreateExcludedTerm(projectId: number) {
  return useCreateTerm<ExcludedTermResponse>(projectId, OPTIONS)
}

export function useDeleteExcludedTerm(projectId: number) {
  return useDeleteTerm(projectId, OPTIONS)
}
