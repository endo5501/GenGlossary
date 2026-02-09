import { Stack, NavLink, Loader } from '@mantine/core'
import {
  IconFiles,
  IconList,
  IconFileDescription,
  IconAlertCircle,
  IconFileCheck,
  IconEye,
  IconSettings,
} from '@tabler/icons-react'
import { Link, useLocation } from '@tanstack/react-router'
import { useCurrentRun } from '../../api/hooks/useRuns'
import { extractProjectId } from '../../utils/extractProjectId'

interface NavItem {
  label: string
  icon: React.ElementType
  basePath: string
  projectScoped: boolean
}

const navItems: NavItem[] = [
  { label: 'Files', icon: IconFiles, basePath: '/files', projectScoped: true },
  { label: 'Terms', icon: IconList, basePath: '/terms', projectScoped: true },
  { label: 'Provisional', icon: IconFileDescription, basePath: '/provisional', projectScoped: true },
  { label: 'Issues', icon: IconAlertCircle, basePath: '/issues', projectScoped: true },
  { label: 'Refined', icon: IconFileCheck, basePath: '/refined', projectScoped: true },
  { label: 'Document Viewer', icon: IconEye, basePath: '/document-viewer', projectScoped: true },
  { label: 'Settings', icon: IconSettings, basePath: '/settings', projectScoped: true },
]

const STEP_TO_MENU: Record<string, string> = {
  extract: '/terms',
  provisional: '/provisional',
  issues: '/issues',
  refined: '/refined',
}

function getPath(basePath: string, projectId: number | undefined, projectScoped: boolean): string {
  if (projectId !== undefined && projectScoped) {
    return `/projects/${projectId}${basePath}`
  }
  return basePath
}

function isActive(pathname: string, basePath: string, projectId: number | undefined, projectScoped: boolean): boolean {
  const targetPath = getPath(basePath, projectId, projectScoped)
  return pathname === targetPath || pathname.startsWith(targetPath + '/')
}

export function LeftNavRail() {
  const location = useLocation()
  const projectId = extractProjectId(location.pathname)
  const { data: run } = useCurrentRun(projectId)

  const isProcessing = (basePath: string): boolean => {
    if (run?.status !== 'running' || !run.current_step) return false
    return STEP_TO_MENU[run.current_step] === basePath
  }

  return (
    <Stack gap={0}>
      {navItems.map((item) => {
        const processing = isProcessing(item.basePath)
        return (
          <NavLink
            key={item.basePath}
            component={Link}
            to={getPath(item.basePath, projectId, item.projectScoped)}
            label={item.label}
            leftSection={
              processing ? <Loader size={20} aria-label="Processing" /> : <item.icon size={20} />
            }
            active={isActive(location.pathname, item.basePath, projectId, item.projectScoped)}
            aria-busy={processing || undefined}
          />
        )
      })}
    </Stack>
  )
}
