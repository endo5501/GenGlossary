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
  renderLoading?: () => ReactNode
  renderEmpty?: () => ReactNode
  renderError?: (error: Error, onRetry?: () => void) => ReactNode
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
  renderLoading,
  renderEmpty,
  renderError,
}: PageContainerProps) {
  const renderContent = (content: ReactNode) => (
    <Box className="page-layout">
      <Group className="action-bar" data-testid="action-bar" p="md">
        {actionBar}
      </Group>
      <Box className="scrollable-content">
        {content}
      </Box>
    </Box>
  )

  if (isLoading) {
    if (renderLoading) {
      return <>{renderLoading()}</>
    }
    return (
      <Center data-testid={loadingTestId} h={200}>
        <Loader />
      </Center>
    )
  }

  if (error) {
    if (renderError) {
      return renderContent(renderError(error, onRetry))
    }
    return renderContent(
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
    )
  }

  if (isEmpty) {
    if (renderEmpty) {
      return renderContent(renderEmpty())
    }
    return renderContent(
      <Center data-testid={emptyTestId} style={{ flex: 1 }}>
        <Text c="dimmed">{emptyMessage}</Text>
      </Center>
    )
  }

  return renderContent(children)
}
