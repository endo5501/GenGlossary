import { AppShell as MantineAppShell, Box } from '@mantine/core'
import { Outlet, useLocation } from '@tanstack/react-router'
import { useQueryClient } from '@tanstack/react-query'
import { useCallback } from 'react'
import { GlobalTopBar } from './GlobalTopBar'
import { LeftNavRail } from './LeftNavRail'
import { LogPanel } from './LogPanel'
import { useCurrentRun, runKeys } from '../../api/hooks'

function extractProjectId(pathname: string): number | undefined {
  const match = pathname.match(/^\/projects\/(\d+)/)
  return match ? Number(match[1]) : undefined
}

export function AppShell() {
  const location = useLocation()
  const projectId = extractProjectId(location.pathname)
  const queryClient = useQueryClient()

  // Get current run to pass runId to LogPanel
  const { data: currentRun } = useCurrentRun(projectId)
  const runId = currentRun?.status === 'running' ? currentRun.id : undefined

  // Invalidate current run cache when SSE stream completes
  const handleRunComplete = useCallback(() => {
    if (projectId !== undefined) {
      queryClient.invalidateQueries({ queryKey: runKeys.current(projectId) })
    }
  }, [queryClient, projectId])

  const hasProject = projectId !== undefined

  return (
    <MantineAppShell
      header={{ height: 60 }}
      navbar={hasProject ? { width: 200, breakpoint: 'sm' } : undefined}
      padding="md"
    >
      <MantineAppShell.Header>
        <GlobalTopBar projectId={projectId} />
      </MantineAppShell.Header>

      {hasProject && (
        <MantineAppShell.Navbar p="xs">
          <LeftNavRail />
        </MantineAppShell.Navbar>
      )}

      <MantineAppShell.Main>
        <Box data-testid="main-content" style={{ height: '100%' }}>
          <Box style={{ minHeight: hasProject ? 'calc(100vh - 60px - 200px - 32px)' : 'calc(100vh - 60px - 32px)' }}>
            <Outlet />
          </Box>
          {hasProject && <LogPanel projectId={projectId} runId={runId} onRunComplete={handleRunComplete} />}
        </Box>
      </MantineAppShell.Main>
    </MantineAppShell>
  )
}
