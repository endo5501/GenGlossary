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
}

const navItems: NavItem[] = [
  { label: 'Files', icon: IconFiles, basePath: '/files' },
  { label: 'Terms', icon: IconList, basePath: '/terms' },
  { label: 'Provisional', icon: IconFileDescription, basePath: '/provisional' },
  { label: 'Issues', icon: IconAlertCircle, basePath: '/issues' },
  { label: 'Refined', icon: IconFileCheck, basePath: '/refined' },
  { label: 'Document Viewer', icon: IconEye, basePath: '/document-viewer' },
  { label: 'Settings', icon: IconSettings, basePath: '/settings' },
]

function extractProjectId(pathname: string): number | undefined {
  const match = pathname.match(/^\/projects\/(\d+)/)
  return match ? Number(match[1]) : undefined
}

function getPath(basePath: string, projectId: number | undefined): string {
  if (projectId !== undefined) {
    return `/projects/${projectId}${basePath}`
  }
  return basePath
}

function isActive(pathname: string, basePath: string, projectId: number | undefined): boolean {
  const targetPath = getPath(basePath, projectId)
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
          to={getPath(item.basePath, projectId)}
          label={item.label}
          leftSection={<item.icon size={20} />}
          active={isActive(location.pathname, item.basePath, projectId)}
        />
      ))}
    </Stack>
  )
}
