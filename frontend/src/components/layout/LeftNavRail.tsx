import { Stack, NavLink } from '@mantine/core'
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

interface NavItem {
  label: string
  icon: React.ElementType
  basePath: string
  projectScoped: boolean
}

const navItems: NavItem[] = [
  { label: 'Files', icon: IconFiles, basePath: '/files', projectScoped: true },
  { label: 'Terms', icon: IconList, basePath: '/terms', projectScoped: false },
  { label: 'Provisional', icon: IconFileDescription, basePath: '/provisional', projectScoped: false },
  { label: 'Issues', icon: IconAlertCircle, basePath: '/issues', projectScoped: false },
  { label: 'Refined', icon: IconFileCheck, basePath: '/refined', projectScoped: false },
  { label: 'Document Viewer', icon: IconEye, basePath: '/document-viewer', projectScoped: true },
  { label: 'Settings', icon: IconSettings, basePath: '/settings', projectScoped: true },
]

function extractProjectId(pathname: string): number | undefined {
  const match = pathname.match(/^\/projects\/(\d+)/)
  return match ? Number(match[1]) : undefined
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

  return (
    <Stack gap={0}>
      {navItems.map((item) => (
        <NavLink
          key={item.basePath}
          component={Link}
          to={getPath(item.basePath, projectId, item.projectScoped)}
          label={item.label}
          leftSection={<item.icon size={20} />}
          active={isActive(location.pathname, item.basePath, projectId, item.projectScoped)}
        />
      ))}
    </Stack>
  )
}
