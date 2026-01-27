import type { RunStatus } from '../api/types'

export const statusColors: Record<RunStatus, string> = {
  pending: 'gray',
  running: 'blue',
  completed: 'green',
  failed: 'red',
  cancelled: 'yellow',
}

export const severityColors: Record<string, string> = {
  low: 'green',
  medium: 'yellow',
  high: 'red',
}

export const issueTypeColors: Record<string, string> = {
  ambiguous: 'orange',
  inconsistent: 'grape',
  missing: 'cyan',
}

export const levelColors: Record<string, string> = {
  info: 'var(--mantine-color-gray-3)',
  warning: 'var(--mantine-color-yellow-5)',
  error: 'var(--mantine-color-red-5)',
}
