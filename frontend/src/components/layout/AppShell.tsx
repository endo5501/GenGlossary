import { AppShell as MantineAppShell, Box } from '@mantine/core'
import { Outlet } from '@tanstack/react-router'
import { GlobalTopBar } from './GlobalTopBar'
import { LeftNavRail } from './LeftNavRail'
import { LogPanel } from './LogPanel'

export function AppShell() {
  return (
    <MantineAppShell
      header={{ height: 60 }}
      navbar={{
        width: 200,
        breakpoint: 'sm',
      }}
      padding="md"
    >
      <MantineAppShell.Header>
        <GlobalTopBar />
      </MantineAppShell.Header>

      <MantineAppShell.Navbar p="xs">
        <LeftNavRail />
      </MantineAppShell.Navbar>

      <MantineAppShell.Main>
        <Box data-testid="main-content" style={{ height: '100%' }}>
          <Box style={{ minHeight: 'calc(100vh - 60px - 200px - 32px)' }}>
            <Outlet />
          </Box>
          <LogPanel />
        </Box>
      </MantineAppShell.Main>
    </MantineAppShell>
  )
}
