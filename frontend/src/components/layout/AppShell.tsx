import { AppShell as MantineAppShell, Box } from '@mantine/core'
import { Outlet, useLocation } from '@tanstack/react-router'
import { useQueryClient } from '@tanstack/react-query'
import { useCallback } from 'react'
import { GlobalTopBar } from './GlobalTopBar'
import { LeftNavRail } from './LeftNavRail'
import { LogPanel } from './LogPanel'
import {
  useCurrentRun,
  runKeys,
  termKeys,
  provisionalKeys,
  issueKeys,
  refinedKeys,
} from '../../api/hooks'

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

  // Invalidate caches when SSE stream completes (run finished)
  // All data lists are refreshed since run completion may affect any of them
  const handleRunComplete = useCallback(() => {
    if (projectId === undefined) return

    queryClient.invalidateQueries({ queryKey: runKeys.current(projectId) })
    queryClient.invalidateQueries({ queryKey: termKeys.list(projectId) })
    queryClient.invalidateQueries({ queryKey: provisionalKeys.list(projectId) })
    queryClient.invalidateQueries({ queryKey: issueKeys.list(projectId) })
    queryClient.invalidateQueries({ queryKey: refinedKeys.list(projectId) })
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
        <Box
          data-testid="main-content"
          style={{
            height: 'calc(100vh - var(--header-height))',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          <Box
            data-testid="scrollable-content"
            style={{
              flex: 1,
              overflow: 'hidden',
              minHeight: 0,
            }}
          >
            <Outlet />
          </Box>
          {hasProject && <LogPanel projectId={projectId} runId={runId} onRunComplete={handleRunComplete} />}
        </Box>
      </MantineAppShell.Main>
    </MantineAppShell>
  )
}
