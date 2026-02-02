import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MantineProvider } from '@mantine/core'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { RouterProvider, createMemoryHistory, createRouter, createRootRoute } from '@tanstack/react-router'
import { LeftNavRail } from '../components/layout/LeftNavRail'

// Mock useCurrentRun hook
vi.mock('../api/hooks/useRuns', () => ({
  useCurrentRun: vi.fn(),
}))

import { useCurrentRun } from '../api/hooks/useRuns'

const mockUseCurrentRun = vi.mocked(useCurrentRun)

async function renderLeftNavRail(initialPath = '/projects/1/files') {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  })
  const rootRoute = createRootRoute({
    component: () => <LeftNavRail />,
  })
  const router = createRouter({
    routeTree: rootRoute,
    history: createMemoryHistory({ initialEntries: [initialPath] }),
  })
  const result = render(
    <QueryClientProvider client={queryClient}>
      <MantineProvider>
        <RouterProvider router={router} />
      </MantineProvider>
    </QueryClientProvider>
  )

  // Wait for router to be ready
  await waitFor(() => {
    expect(screen.getByRole('link', { name: /files/i })).toBeInTheDocument()
  })

  return result
}

describe('LeftNavRail', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Processing indicator', () => {
    it('should show spinner on Terms when current_step is extract', async () => {
      mockUseCurrentRun.mockReturnValue({
        data: { status: 'running', current_step: 'extract' },
        isLoading: false,
        error: null,
      } as ReturnType<typeof useCurrentRun>)

      await renderLeftNavRail()

      const termsLink = screen.getByRole('link', { name: /terms/i })
      expect(termsLink.querySelector('.mantine-Loader-root')).toBeInTheDocument()
    })

    it('should show spinner on Provisional when current_step is provisional', async () => {
      mockUseCurrentRun.mockReturnValue({
        data: { status: 'running', current_step: 'provisional' },
        isLoading: false,
        error: null,
      } as ReturnType<typeof useCurrentRun>)

      await renderLeftNavRail()

      const provisionalLink = screen.getByRole('link', { name: /provisional/i })
      expect(provisionalLink.querySelector('.mantine-Loader-root')).toBeInTheDocument()
    })

    it('should show spinner on Issues when current_step is issues', async () => {
      mockUseCurrentRun.mockReturnValue({
        data: { status: 'running', current_step: 'issues' },
        isLoading: false,
        error: null,
      } as ReturnType<typeof useCurrentRun>)

      await renderLeftNavRail()

      const issuesLink = screen.getByRole('link', { name: /issues/i })
      expect(issuesLink.querySelector('.mantine-Loader-root')).toBeInTheDocument()
    })

    it('should show spinner on Refined when current_step is refined', async () => {
      mockUseCurrentRun.mockReturnValue({
        data: { status: 'running', current_step: 'refined' },
        isLoading: false,
        error: null,
      } as ReturnType<typeof useCurrentRun>)

      await renderLeftNavRail()

      const refinedLink = screen.getByRole('link', { name: /refined/i })
      expect(refinedLink.querySelector('.mantine-Loader-root')).toBeInTheDocument()
    })

    it('should NOT show spinner when status is not running', async () => {
      mockUseCurrentRun.mockReturnValue({
        data: { status: 'completed', current_step: 'extract' },
        isLoading: false,
        error: null,
      } as ReturnType<typeof useCurrentRun>)

      await renderLeftNavRail()

      const termsLink = screen.getByRole('link', { name: /terms/i })
      expect(termsLink.querySelector('.mantine-Loader-root')).not.toBeInTheDocument()
    })

    it('should NOT show spinner when current_step is null', async () => {
      mockUseCurrentRun.mockReturnValue({
        data: { status: 'running', current_step: null },
        isLoading: false,
        error: null,
      } as ReturnType<typeof useCurrentRun>)

      await renderLeftNavRail()

      const termsLink = screen.getByRole('link', { name: /terms/i })
      expect(termsLink.querySelector('.mantine-Loader-root')).not.toBeInTheDocument()
    })

    it('should NOT show spinner on Files (not a processing step)', async () => {
      mockUseCurrentRun.mockReturnValue({
        data: { status: 'running', current_step: 'extract' },
        isLoading: false,
        error: null,
      } as ReturnType<typeof useCurrentRun>)

      await renderLeftNavRail()

      const filesLink = screen.getByRole('link', { name: /files/i })
      expect(filesLink.querySelector('.mantine-Loader-root')).not.toBeInTheDocument()
    })

    it('should set aria-busy on processing menu item', async () => {
      mockUseCurrentRun.mockReturnValue({
        data: { status: 'running', current_step: 'extract' },
        isLoading: false,
        error: null,
      } as ReturnType<typeof useCurrentRun>)

      await renderLeftNavRail()

      const termsLink = screen.getByRole('link', { name: /terms/i })
      expect(termsLink).toHaveAttribute('aria-busy', 'true')
    })

    it('should NOT set aria-busy on non-processing menu item', async () => {
      mockUseCurrentRun.mockReturnValue({
        data: { status: 'running', current_step: 'extract' },
        isLoading: false,
        error: null,
      } as ReturnType<typeof useCurrentRun>)

      await renderLeftNavRail()

      const filesLink = screen.getByRole('link', { name: /files/i })
      expect(filesLink).not.toHaveAttribute('aria-busy', 'true')
    })
  })
})
