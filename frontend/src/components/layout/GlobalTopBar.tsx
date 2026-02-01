import { Group, Title, Badge, Button, Select, Box, Text, Anchor } from '@mantine/core'
import { IconPlayerPlay, IconPlayerStop, IconArrowLeft } from '@tabler/icons-react'
import { useState } from 'react'
import { Link, useNavigate } from '@tanstack/react-router'
import { useCurrentRun, useStartRun, useCancelRun } from '../../api/hooks'
import type { RunScope, RunStatus } from '../../api/types'
import { statusColors } from '../../utils/colors'

interface GlobalTopBarProps {
  projectId?: number
  status?: RunStatus
  onRun?: (scope: RunScope) => void
  onStop?: () => void
}

const scopeOptions = [
  { value: 'full', label: 'Full Pipeline' },
  { value: 'extract', label: 'Extract Only' },
  { value: 'generate', label: 'Generate Only' },
  { value: 'review', label: 'Review Only' },
  { value: 'refine', label: 'Refine Only' },
]

const isRunScope = (value: string): value is RunScope =>
  ['full', 'extract', 'generate', 'review', 'refine'].includes(value)

export function GlobalTopBar({
  projectId,
  status: propStatus,
  onRun: propOnRun,
  onStop: propOnStop,
}: GlobalTopBarProps) {
  const [scope, setScope] = useState<RunScope>('full')
  const navigate = useNavigate()

  const { data: currentRun } = useCurrentRun(projectId)
  const startRun = useStartRun(projectId ?? 0)
  const cancelRun = useCancelRun(projectId ?? 0)

  const status = projectId && currentRun ? currentRun.status : (propStatus ?? 'pending')
  const runId = currentRun?.id
  const progress = currentRun?.progress_total
    ? { current: currentRun.progress_current, total: currentRun.progress_total }
    : null

  const navigateToHome = () => navigate({ to: '/' })

  const handleRun = () => {
    projectId ? startRun.mutate({ scope }) : propOnRun?.(scope)
  }

  const handleStop = () => {
    projectId && runId ? cancelRun.mutate(runId) : propOnStop?.()
  }

  // Home page: simple header without project controls
  if (projectId === undefined) {
    return (
      <Group h="100%" px="md" justify="space-between">
        <Title order={4}>GenGlossary</Title>
      </Group>
    )
  }

  // Project detail page: full header with status and controls
  return (
    <Group h="100%" px="md" justify="space-between">
      <Group>
        <Button
          variant="subtle"
          size="compact-sm"
          leftSection={<IconArrowLeft size={16} />}
          onClick={navigateToHome}
          aria-label="Back"
        >
          Back
        </Button>
        <Anchor component={Link} to="/" underline="never" c="inherit">
          <Title order={4}>GenGlossary</Title>
        </Anchor>
        <Badge
          color={statusColors[status]}
          data-testid="status-badge"
        >
          {status}
        </Badge>
        {status === 'running' && progress && progress.total > 0 && (
          <Text size="sm" c="dimmed">
            {progress.current} / {progress.total}
          </Text>
        )}
      </Group>

      <Group>
        <Button
          leftSection={<IconPlayerPlay size={16} />}
          variant="filled"
          color="green"
          onClick={handleRun}
          disabled={status === 'running' || startRun.isPending}
          loading={startRun.isPending}
          aria-label="Run"
        >
          Run
        </Button>
        <Button
          leftSection={<IconPlayerStop size={16} />}
          variant="outline"
          color="red"
          onClick={handleStop}
          disabled={status !== 'running' || runId === undefined}
          loading={cancelRun.isPending}
          aria-label="Stop"
        >
          Stop
        </Button>
        <Box data-testid="scope-selector">
          <Select
            value={scope}
            onChange={(value) => {
              if (value && isRunScope(value)) {
                setScope(value)
              }
            }}
            data={scopeOptions}
            allowDeselect={false}
            w={180}
            aria-label="Scope"
          />
        </Box>
      </Group>
    </Group>
  )
}
