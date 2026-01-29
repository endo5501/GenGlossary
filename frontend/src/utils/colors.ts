import type { RunStatus } from '../api/types'

export const statusColors: Record<RunStatus, string> = {
  pending: 'gray',
  running: 'blue',
  completed: 'green',
  failed: 'red',
  cancelled: 'yellow',
}

export function getStatusColor(status: string): string {
  return statusColors[status as RunStatus] ?? 'gray'
}

export type IssueType = 'unclear' | 'contradiction' | 'missing_relation' | 'unnecessary'
export const issueTypeColors: Record<IssueType, string> = {
  unclear: 'orange',
  contradiction: 'grape',
  missing_relation: 'cyan',
  unnecessary: 'gray',
}

export function getIssueTypeColor(issueType: string): string {
  return issueTypeColors[issueType as IssueType] ?? 'gray'
}

export const levelColors: Record<string, string> = {
  info: 'var(--mantine-color-gray-3)',
  warning: 'var(--mantine-color-yellow-5)',
  error: 'var(--mantine-color-red-5)',
}
