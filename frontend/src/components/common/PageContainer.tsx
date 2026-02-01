import { Box, Group, Center, Text, Loader, Button } from '@mantine/core'
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
      <Box style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
        <Group
          data-testid="action-bar"
          p="md"
          style={{ flexShrink: 0, borderBottom: '1px solid var(--mantine-color-gray-3)' }}
        >
          {actionBar}
        </Group>
        <Center data-testid="page-error" style={{ flex: 1 }}>
          <Box style={{ textAlign: 'center' }}>
            <Text c="red">Error: {error.message}</Text>
            {onRetry && (
              <Button variant="outline" onClick={onRetry} mt="md">
                Retry
              </Button>
            )}
          </Box>
        </Center>
      </Box>
    )
  }

  if (isEmpty) {
    return (
      <Box style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
        <Group
          data-testid="action-bar"
          p="md"
          style={{ flexShrink: 0, borderBottom: '1px solid var(--mantine-color-gray-3)' }}
        >
          {actionBar}
        </Group>
        <Center data-testid={emptyTestId} style={{ flex: 1 }}>
          <Text c="dimmed">{emptyMessage}</Text>
        </Center>
      </Box>
    )
  }

  return (
    <Box style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Group
        data-testid="action-bar"
        p="md"
        style={{ flexShrink: 0, borderBottom: '1px solid var(--mantine-color-gray-3)' }}
      >
        {actionBar}
      </Group>
      <Box style={{ flex: 1, overflowY: 'auto', minHeight: 0, padding: 'var(--mantine-spacing-md)' }}>
        {children}
      </Box>
    </Box>
  )
}
