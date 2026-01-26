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
  path: string
}

const navItems: NavItem[] = [
  { label: 'Files', icon: IconFiles, path: '/files' },
  { label: 'Terms', icon: IconList, path: '/terms' },
  { label: 'Provisional', icon: IconFileDescription, path: '/provisional' },
  { label: 'Issues', icon: IconAlertCircle, path: '/issues' },
  { label: 'Refined', icon: IconFileCheck, path: '/refined' },
  { label: 'Document Viewer', icon: IconEye, path: '/document-viewer' },
  { label: 'Settings', icon: IconSettings, path: '/settings' },
]

export function LeftNavRail() {
  const location = useLocation()

  return (
    <Stack gap={0}>
      {navItems.map((item) => (
        <NavLink
          key={item.path}
          component={Link}
          to={item.path}
          label={item.label}
          leftSection={<item.icon size={20} />}
          active={location.pathname === item.path}
        />
      ))}
    </Stack>
  )
}
