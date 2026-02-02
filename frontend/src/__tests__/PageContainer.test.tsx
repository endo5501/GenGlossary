import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MantineProvider } from '@mantine/core'
import { PageContainer } from '../components/common/PageContainer'

const renderPageContainer = (props: Partial<Parameters<typeof PageContainer>[0]> = {}) => {
  const defaultProps = {
    isLoading: false,
    isEmpty: false,
    emptyMessage: 'No items',
    actionBar: <button>Action</button>,
    children: <div data-testid="content">Content</div>,
  }
  return render(
    <MantineProvider>
      <PageContainer {...defaultProps} {...props} />
    </MantineProvider>
  )
}

describe('PageContainer', () => {
  describe('default behavior (backward compatibility)', () => {
    it('should render action bar and content in normal state', () => {
      renderPageContainer()
      expect(screen.getByTestId('action-bar')).toBeInTheDocument()
      expect(screen.getByTestId('content')).toBeInTheDocument()
    })

    it('should render default loading state', () => {
      renderPageContainer({ isLoading: true })
      expect(screen.getByTestId('page-loading')).toBeInTheDocument()
    })

    it('should render default empty state', () => {
      renderPageContainer({ isEmpty: true })
      expect(screen.getByTestId('action-bar')).toBeInTheDocument()
      expect(screen.getByText('No items')).toBeInTheDocument()
    })

    it('should render default error state', () => {
      renderPageContainer({ error: new Error('Test error') })
      expect(screen.getByTestId('action-bar')).toBeInTheDocument()
      expect(screen.getByTestId('page-error')).toBeInTheDocument()
      expect(screen.getByText('Error: Test error')).toBeInTheDocument()
    })

    it('should render retry button when error and onRetry provided', async () => {
      const user = userEvent.setup()
      let retryCalled = false
      renderPageContainer({
        error: new Error('Test error'),
        onRetry: () => { retryCalled = true },
      })

      const retryButton = screen.getByRole('button', { name: /retry/i })
      await user.click(retryButton)

      expect(retryCalled).toBe(true)
    })
  })

  describe('render props (custom rendering)', () => {
    it('should use renderLoading when provided', () => {
      renderPageContainer({
        isLoading: true,
        renderLoading: () => <div data-testid="custom-loading">Custom Loading</div>,
      })
      expect(screen.getByTestId('custom-loading')).toBeInTheDocument()
      expect(screen.queryByTestId('page-loading')).not.toBeInTheDocument()
    })

    it('should use renderEmpty when provided', () => {
      renderPageContainer({
        isEmpty: true,
        renderEmpty: () => <div data-testid="custom-empty">Custom Empty</div>,
      })
      expect(screen.getByTestId('action-bar')).toBeInTheDocument()
      expect(screen.getByTestId('custom-empty')).toBeInTheDocument()
      expect(screen.queryByText('No items')).not.toBeInTheDocument()
    })

    it('should use renderError when provided', () => {
      const testError = new Error('Test error')
      renderPageContainer({
        error: testError,
        renderError: (error) => <div data-testid="custom-error">Custom: {error.message}</div>,
      })
      expect(screen.getByTestId('action-bar')).toBeInTheDocument()
      expect(screen.getByTestId('custom-error')).toBeInTheDocument()
      expect(screen.getByText('Custom: Test error')).toBeInTheDocument()
    })

    it('should pass onRetry to renderError', async () => {
      const user = userEvent.setup()
      let retryCalled = false
      renderPageContainer({
        error: new Error('Test error'),
        onRetry: () => { retryCalled = true },
        renderError: (_error, onRetry) => (
          <button onClick={onRetry} data-testid="custom-retry">Custom Retry</button>
        ),
      })

      await user.click(screen.getByTestId('custom-retry'))
      expect(retryCalled).toBe(true)
    })
  })

  describe('layout structure', () => {
    it('should use page-layout class on container', () => {
      const { container } = renderPageContainer()
      expect(container.querySelector('.page-layout')).toBeInTheDocument()
    })

    it('should use action-bar class on action bar', () => {
      const { container } = renderPageContainer()
      expect(container.querySelector('.action-bar')).toBeInTheDocument()
    })

    it('should use scrollable-content class on content area', () => {
      const { container } = renderPageContainer()
      expect(container.querySelector('.scrollable-content')).toBeInTheDocument()
    })
  })
})
