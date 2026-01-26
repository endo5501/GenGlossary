import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MantineProvider } from '@mantine/core'
import { renderApp } from './test-utils'
import { GlobalTopBar } from '../components/layout/GlobalTopBar'

const renderGlobalTopBar = (props = {}) => {
  return render(
    <MantineProvider>
      <GlobalTopBar {...props} />
    </MantineProvider>
  )
}

describe('AppShell', () => {
  describe('GlobalTopBar', () => {
    it('should display project name', async () => {
      await renderApp()
      expect(screen.getByText('GenGlossary')).toBeInTheDocument()
    })

    it('should display status badge', async () => {
      await renderApp()
      expect(screen.getByTestId('status-badge')).toBeInTheDocument()
    })

    it('should display Run button', async () => {
      await renderApp()
      expect(screen.getByRole('button', { name: /run/i })).toBeInTheDocument()
    })

    it('should display Stop button', async () => {
      await renderApp()
      expect(screen.getByRole('button', { name: /stop/i })).toBeInTheDocument()
    })

    it('should display scope selector', async () => {
      await renderApp()
      expect(screen.getByTestId('scope-selector')).toBeInTheDocument()
    })
  })

  describe('GlobalTopBar interactions', () => {
    it('should call onRun with default scope when Run button is clicked', async () => {
      const onRun = vi.fn()
      renderGlobalTopBar({ onRun })
      const user = userEvent.setup()

      await user.click(screen.getByRole('button', { name: /run/i }))

      expect(onRun).toHaveBeenCalledWith('full')
    })

    it('should call onStop when Stop button is clicked while running', async () => {
      const onStop = vi.fn()
      renderGlobalTopBar({ status: 'running', onStop })
      const user = userEvent.setup()

      await user.click(screen.getByRole('button', { name: /stop/i }))

      expect(onStop).toHaveBeenCalled()
    })

    it('should disable Run button when status is running', () => {
      renderGlobalTopBar({ status: 'running' })

      expect(screen.getByRole('button', { name: /run/i })).toBeDisabled()
    })

    it('should disable Stop button when status is not running', () => {
      renderGlobalTopBar({ status: 'pending' })

      expect(screen.getByRole('button', { name: /stop/i })).toBeDisabled()
    })

    it('should enable Stop button when status is running', () => {
      renderGlobalTopBar({ status: 'running' })

      expect(screen.getByRole('button', { name: /stop/i })).toBeEnabled()
    })
  })

  describe('LeftNavRail', () => {
    it('should display Files navigation link', async () => {
      await renderApp()
      expect(screen.getByRole('link', { name: /files/i })).toBeInTheDocument()
    })

    it('should display Terms navigation link', async () => {
      await renderApp()
      expect(screen.getByRole('link', { name: /terms/i })).toBeInTheDocument()
    })

    it('should display Provisional navigation link', async () => {
      await renderApp()
      expect(screen.getByRole('link', { name: /provisional/i })).toBeInTheDocument()
    })

    it('should display Issues navigation link', async () => {
      await renderApp()
      expect(screen.getByRole('link', { name: /issues/i })).toBeInTheDocument()
    })

    it('should display Refined navigation link', async () => {
      await renderApp()
      expect(screen.getByRole('link', { name: /refined/i })).toBeInTheDocument()
    })

    it('should display Document Viewer navigation link', async () => {
      await renderApp()
      expect(screen.getByRole('link', { name: /document/i })).toBeInTheDocument()
    })

    it('should display Settings navigation link', async () => {
      await renderApp()
      expect(screen.getByRole('link', { name: /settings/i })).toBeInTheDocument()
    })
  })

  describe('MainContent', () => {
    it('should display main content area', async () => {
      await renderApp()
      expect(screen.getByTestId('main-content')).toBeInTheDocument()
    })
  })

  describe('LogPanel', () => {
    it('should display log panel placeholder', async () => {
      await renderApp()
      expect(screen.getByTestId('log-panel')).toBeInTheDocument()
    })
  })
})
