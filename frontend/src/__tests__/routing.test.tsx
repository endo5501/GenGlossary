import { describe, expect, it } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderApp } from './test-utils'

describe('Routing', () => {
  describe('Router initialization', () => {
    it('should initialize router without errors', async () => {
      await expect(renderApp()).resolves.not.toThrow()
    })

    it('should render root route', async () => {
      await renderApp('/')
      expect(screen.getByTestId('main-content')).toBeInTheDocument()
    })
  })

  describe('Route navigation (from project page)', () => {
    const navigationRoutes = [
      { path: '/projects/1/files', name: /files/i },
      { path: '/projects/1/terms', name: /terms/i },
      { path: '/projects/1/provisional', name: /provisional/i },
      { path: '/projects/1/issues', name: /issues/i },
      { path: '/projects/1/refined', name: /refined/i },
      { path: '/projects/1/document-viewer', name: /document/i },
      { path: '/projects/1/settings', name: /settings/i },
    ]

    it.each(navigationRoutes)('should navigate to $path', async ({ path, name }) => {
      // Start from a project page to have sidebar navigation available
      const { router } = await renderApp('/projects/1/files')
      const user = userEvent.setup()

      const link = screen.getByRole('link', { name })
      await user.click(link)

      await waitFor(() => {
        expect(router.state.location.pathname).toBe(path)
      })
    })
  })

  describe('Direct route access', () => {
    it('should render files page when navigating directly to /files', async () => {
      await renderApp('/files')
      expect(screen.getByTestId('main-content')).toBeInTheDocument()
    })

    it('should render terms page when navigating directly to /terms', async () => {
      await renderApp('/terms')
      expect(screen.getByTestId('main-content')).toBeInTheDocument()
    })

    it('should render provisional page when navigating directly to /provisional', async () => {
      await renderApp('/provisional')
      expect(screen.getByTestId('main-content')).toBeInTheDocument()
    })

    it('should render issues page when navigating directly to /issues', async () => {
      await renderApp('/issues')
      expect(screen.getByTestId('main-content')).toBeInTheDocument()
    })

    it('should render refined page when navigating directly to /refined', async () => {
      await renderApp('/refined')
      expect(screen.getByTestId('main-content')).toBeInTheDocument()
    })

    it('should render document viewer page when navigating directly to /document-viewer', async () => {
      await renderApp('/document-viewer')
      expect(screen.getByTestId('main-content')).toBeInTheDocument()
    })

    it('should render settings page when navigating directly to /settings', async () => {
      await renderApp('/settings')
      expect(screen.getByTestId('main-content')).toBeInTheDocument()
    })
  })
})
