import { Stack, Group, Center, Text, Loader } from '@mantine/core'
import type { ReactNode } from 'react'

interface PageContainerProps {
  isLoading: boolean
  isEmpty: boolean
  emptyMessage: string
  actionBar: ReactNode
  children: ReactNode
  loadingTestId?: string
  emptyTestId?: string
}

export function PageContainer({
  isLoading,
  isEmpty,
  emptyMessage,
  actionBar,
  children,
  loadingTestId = 'page-loading',
  emptyTestId = 'page-empty',
}: PageContainerProps) {
  if (isLoading) {
    return (
      <Center data-testid={loadingTestId} h={200}>
        <Loader />
      </Center>
    )
  }

  if (isEmpty) {
    return (
      <Stack>
        <Group>{actionBar}</Group>
        <Center data-testid={emptyTestId} h={200}>
          <Text c="dimmed">{emptyMessage}</Text>
        </Center>
      </Stack>
    )
  }

  return (
    <Stack>
      <Group>{actionBar}</Group>
      {children}
    </Stack>
  )
}
