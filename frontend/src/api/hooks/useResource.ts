import { useMutation, useQuery, useQueryClient, type QueryKey } from '@tanstack/react-query'

interface UseResourceListOptions<T> {
  queryKey: QueryKey
  queryFn: () => Promise<T[]>
  enabled?: boolean
}

interface UseResourceDetailOptions<T> {
  queryKey: QueryKey
  queryFn: () => Promise<T>
  enabled?: boolean
}

interface UseMutationWithInvalidateOptions<TData, TVariables> {
  mutationFn: (variables: TVariables) => Promise<TData>
  invalidateKeys: QueryKey[]
}

export function useResourceList<T>({ queryKey, queryFn, enabled = true }: UseResourceListOptions<T>) {
  return useQuery({
    queryKey,
    queryFn,
    enabled,
  })
}

export function useResourceDetail<T>({ queryKey, queryFn, enabled = true }: UseResourceDetailOptions<T>) {
  return useQuery({
    queryKey,
    queryFn,
    enabled,
  })
}

export function useMutationWithInvalidate<TData, TVariables>({
  mutationFn,
  invalidateKeys,
}: UseMutationWithInvalidateOptions<TData, TVariables>) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn,
    onSuccess: () => {
      invalidateKeys.forEach((key) => {
        queryClient.invalidateQueries({ queryKey: key })
      })
    },
  })
}
