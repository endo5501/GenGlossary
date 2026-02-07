import type { RequiredTermResponse } from '../types'
import { useTermsList, useCreateTerm, useDeleteTerm } from './useTermsCrud'

const OPTIONS = {
  apiPath: 'required-terms',
  queryKeyPrefix: 'requiredTerms',
} as const

export const requiredTermKeys = {
  all: ['requiredTerms'] as const,
  lists: () => [...requiredTermKeys.all, 'list'] as const,
  list: (projectId: number) => [...requiredTermKeys.lists(), projectId] as const,
}

export function useRequiredTerms(projectId: number | undefined) {
  const { keys: _keys, ...result } = useTermsList<RequiredTermResponse>(projectId, OPTIONS)
  return result
}

export function useCreateRequiredTerm(projectId: number) {
  return useCreateTerm<RequiredTermResponse>(projectId, OPTIONS)
}

export function useDeleteRequiredTerm(projectId: number) {
  return useDeleteTerm(projectId, OPTIONS)
}
