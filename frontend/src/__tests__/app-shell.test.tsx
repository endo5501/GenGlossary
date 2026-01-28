import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MantineProvider } from '@mantine/core'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { renderApp } from './test-utils'
import { GlobalTopBar } from '../components/layout/GlobalTopBar'

const renderGlobalTopBar = (props = {}) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <MantineProvider>
        <GlobalTopBar {...props} />
      </MantineProvider>
    </QueryClientProvider>
  )
}

describe('AppShell', () => {
  describe('Home page layout (no projectId)', () => {
    it('should display GenGlossary title', async () => {
      await renderApp('/')
      expect(screen.getByText('GenGlossary')).toBeInTheDocument()
    })

    it('should NOT display status badge', async () => {
      await renderApp('/')
      expect(screen.queryByTestId('status-badge')).not.toBeInTheDocument()
    })

    it('should NOT display Run button', async () => {
      await renderApp('/')
      expect(screen.queryByRole('button', { name: /run/i })).not.toBeInTheDocument()
    })

    it('should NOT display Stop button', async () => {
      await renderApp('/')
      expect(screen.queryByRole('button', { name: /stop/i })).not.toBeInTheDocument()
    })

    it('should NOT display scope selector', async () => {
      await renderApp('/')
      expect(screen.queryByTestId('scope-selector')).not.toBeInTheDocument()
    })

    it('should NOT display sidebar navigation', async () => {
      await renderApp('/')
      expect(screen.queryByRole('link', { name: /files/i })).not.toBeInTheDocument()
      expect(screen.queryByRole('link', { name: /terms/i })).not.toBeInTheDocument()
      expect(screen.queryByRole('link', { name: /settings/i })).not.toBeInTheDocument()
    })

    it('should NOT display log panel', async () => {
      await renderApp('/')
      expect(screen.queryByTestId('log-panel')).not.toBeInTheDocument()
    })
  })

  describe('Project detail page layout (with projectId)', () => {
    it('should display GenGlossary title', async () => {
      await renderApp('/projects/1/files')
      expect(screen.getByText('GenGlossary')).toBeInTheDocument()
    })

    it('should display status badge', async () => {
      await renderApp('/projects/1/files')
      expect(screen.getByTestId('status-badge')).toBeInTheDocument()
    })

    it('should display Run button', async () => {
      await renderApp('/projects/1/files')
      expect(screen.getByRole('button', { name: /run/i })).toBeInTheDocument()
    })

    it('should display Stop button', async () => {
      await renderApp('/projects/1/files')
      expect(screen.getByRole('button', { name: /stop/i })).toBeInTheDocument()
    })

    it('should display scope selector', async () => {
      await renderApp('/projects/1/files')
      expect(screen.getByTestId('scope-selector')).toBeInTheDocument()
    })

    it('should display sidebar navigation', async () => {
      await renderApp('/projects/1/files')
      expect(screen.getByRole('link', { name: /files/i })).toBeInTheDocument()
      expect(screen.getByRole('link', { name: /terms/i })).toBeInTheDocument()
      expect(screen.getByRole('link', { name: /settings/i })).toBeInTheDocument()
    })

    it('should display log panel', async () => {
      await renderApp('/projects/1/files')
      expect(screen.getByTestId('log-panel')).toBeInTheDocument()
    })
  })

  describe('GlobalTopBar button states (with projectId)', () => {
    it('should disable Run button when status is running', () => {
      renderGlobalTopBar({ projectId: 1, status: 'running' })

      expect(screen.getByRole('button', { name: /run/i })).toBeDisabled()
    })

    it('should disable Stop button when status is not running', () => {
      renderGlobalTopBar({ projectId: 1, status: 'pending' })

      expect(screen.getByRole('button', { name: /stop/i })).toBeDisabled()
    })

    it('should disable Stop button when status is running but runId is undefined', () => {
      // When status is running but runId is not yet available, Stop button should be disabled
      renderGlobalTopBar({ projectId: 1, status: 'running' })

      expect(screen.getByRole('button', { name: /stop/i })).toBeDisabled()
    })
  })

  describe('LeftNavRail (on project page)', () => {
    it('should display Files navigation link', async () => {
      await renderApp('/projects/1/files')
      expect(screen.getByRole('link', { name: /files/i })).toBeInTheDocument()
    })

    it('should display Terms navigation link', async () => {
      await renderApp('/projects/1/files')
      expect(screen.getByRole('link', { name: /terms/i })).toBeInTheDocument()
    })

    it('should display Provisional navigation link', async () => {
      await renderApp('/projects/1/files')
      expect(screen.getByRole('link', { name: /provisional/i })).toBeInTheDocument()
    })

    it('should display Issues navigation link', async () => {
      await renderApp('/projects/1/files')
      expect(screen.getByRole('link', { name: /issues/i })).toBeInTheDocument()
    })

    it('should display Refined navigation link', async () => {
      await renderApp('/projects/1/files')
      expect(screen.getByRole('link', { name: /refined/i })).toBeInTheDocument()
    })

    it('should display Document Viewer navigation link', async () => {
      await renderApp('/projects/1/files')
      expect(screen.getByRole('link', { name: /document/i })).toBeInTheDocument()
    })

    it('should display Settings navigation link', async () => {
      await renderApp('/projects/1/files')
      expect(screen.getByRole('link', { name: /settings/i })).toBeInTheDocument()
    })
  })

  describe('MainContent', () => {
    it('should display main content area on home page', async () => {
      await renderApp('/')
      expect(screen.getByTestId('main-content')).toBeInTheDocument()
    })

    it('should display main content area on project page', async () => {
      await renderApp('/projects/1/files')
      expect(screen.getByTestId('main-content')).toBeInTheDocument()
    })
  })

  describe('LogPanel (on project page)', () => {
    it('should display log panel on project page', async () => {
      await renderApp('/projects/1/files')
      expect(screen.getByTestId('log-panel')).toBeInTheDocument()
    })
  })
})
