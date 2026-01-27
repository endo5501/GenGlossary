import { Stack, Group, Center, Text, Loader, Button } from '@mantine/core'
import type { ReactNode } from 'react'

interface PageContainerProps {
  isLoading: boolean
  isEmpty: boolean
  emptyMessage: string
  actionBar: ReactNode
  children: ReactNode
  loadingTestId?: string
  emptyTestId?: string
  error?: Error | null
  onRetry?: () => void
}

export function PageContainer({
  isLoading,
  isEmpty,
  emptyMessage,
  actionBar,
  children,
  loadingTestId = 'page-loading',
  emptyTestId = 'page-empty',
  error,
  onRetry,
}: PageContainerProps) {
  if (isLoading) {
    return (
      <Center data-testid={loadingTestId} h={200}>
        <Loader />
      </Center>
    )
  }

  if (error) {
    return (
      <Stack>
        <Group>{actionBar}</Group>
        <Center data-testid="page-error" h={200}>
          <Stack align="center">
            <Text c="red">Error: {error.message}</Text>
            {onRetry && (
              <Button variant="outline" onClick={onRetry}>
                Retry
              </Button>
            )}
          </Stack>
        </Center>
      </Stack>
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
