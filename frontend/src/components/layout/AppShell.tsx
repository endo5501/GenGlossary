import { AppShell as MantineAppShell, Box } from '@mantine/core'
import { Outlet, useLocation } from '@tanstack/react-router'
import { GlobalTopBar } from './GlobalTopBar'
import { LeftNavRail } from './LeftNavRail'
import { LogPanel } from './LogPanel'
import { useCurrentRun } from '../../api/hooks'

function extractProjectId(pathname: string): number | undefined {
  const match = pathname.match(/^\/projects\/(\d+)/)
  return match ? Number(match[1]) : undefined
}

export function AppShell() {
  const location = useLocation()
  const projectId = extractProjectId(location.pathname)

  // Get current run to pass runId to LogPanel
  const { data: currentRun } = useCurrentRun(projectId)
  const runId = currentRun?.status === 'running' ? currentRun.id : undefined

  return (
    <MantineAppShell
      header={{ height: 60 }}
      navbar={projectId ? { width: 200, breakpoint: 'sm' } : undefined}
      padding="md"
    >
      <MantineAppShell.Header>
        <GlobalTopBar projectId={projectId} />
      </MantineAppShell.Header>

      {projectId && (
        <MantineAppShell.Navbar p="xs">
          <LeftNavRail />
        </MantineAppShell.Navbar>
      )}

      <MantineAppShell.Main>
        <Box data-testid="main-content" style={{ height: '100%' }}>
          <Box style={{ minHeight: projectId ? 'calc(100vh - 60px - 200px - 32px)' : 'calc(100vh - 60px - 32px)' }}>
            <Outlet />
          </Box>
          {projectId && <LogPanel projectId={projectId} runId={runId} />}
        </Box>
      </MantineAppShell.Main>
    </MantineAppShell>
  )
}
