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

  describe('Route navigation', () => {
    it('should navigate to /files', async () => {
      const { router } = await renderApp()
      const user = userEvent.setup()

      const filesLink = screen.getByRole('link', { name: /files/i })
      await user.click(filesLink)

      await waitFor(() => {
        expect(router.state.location.pathname).toBe('/files')
      })
    })

    it('should navigate to /terms', async () => {
      const { router } = await renderApp()
      const user = userEvent.setup()

      const termsLink = screen.getByRole('link', { name: /terms/i })
      await user.click(termsLink)

      await waitFor(() => {
        expect(router.state.location.pathname).toBe('/terms')
      })
    })

    it('should navigate to /provisional', async () => {
      const { router } = await renderApp()
      const user = userEvent.setup()

      const provisionalLink = screen.getByRole('link', { name: /provisional/i })
      await user.click(provisionalLink)

      await waitFor(() => {
        expect(router.state.location.pathname).toBe('/provisional')
      })
    })

    it('should navigate to /issues', async () => {
      const { router } = await renderApp()
      const user = userEvent.setup()

      const issuesLink = screen.getByRole('link', { name: /issues/i })
      await user.click(issuesLink)

      await waitFor(() => {
        expect(router.state.location.pathname).toBe('/issues')
      })
    })

    it('should navigate to /refined', async () => {
      const { router } = await renderApp()
      const user = userEvent.setup()

      const refinedLink = screen.getByRole('link', { name: /refined/i })
      await user.click(refinedLink)

      await waitFor(() => {
        expect(router.state.location.pathname).toBe('/refined')
      })
    })

    it('should navigate to /document-viewer', async () => {
      const { router } = await renderApp()
      const user = userEvent.setup()

      const docViewerLink = screen.getByRole('link', { name: /document/i })
      await user.click(docViewerLink)

      await waitFor(() => {
        expect(router.state.location.pathname).toBe('/document-viewer')
      })
    })

    it('should navigate to /settings', async () => {
      const { router } = await renderApp()
      const user = userEvent.setup()

      const settingsLink = screen.getByRole('link', { name: /settings/i })
      await user.click(settingsLink)

      await waitFor(() => {
        expect(router.state.location.pathname).toBe('/settings')
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
