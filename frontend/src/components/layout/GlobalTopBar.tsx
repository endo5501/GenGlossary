import { Group, Title, Badge, Button, Select, Box } from '@mantine/core'
import { IconPlayerPlay, IconPlayerStop } from '@tabler/icons-react'
import { useState } from 'react'
import type { RunScope, RunStatus } from '../../api/types'

interface GlobalTopBarProps {
  status?: RunStatus
  onRun?: (scope: RunScope) => void
  onStop?: () => void
}

const statusColors: Record<RunStatus, string> = {
  pending: 'gray',
  running: 'blue',
  completed: 'green',
  failed: 'red',
  cancelled: 'yellow',
}

const scopeOptions = [
  { value: 'full', label: 'Full Pipeline' },
  { value: 'from_terms', label: 'From Terms' },
  { value: 'provisional_to_refined', label: 'Provisional to Refined' },
]

const isRunScope = (value: string): value is RunScope =>
  ['full', 'from_terms', 'provisional_to_refined'].includes(value)

export function GlobalTopBar({
  status = 'pending',
  onRun,
  onStop,
}: GlobalTopBarProps) {
  const [scope, setScope] = useState<RunScope>('full')

  const handleRun = () => {
    onRun?.(scope)
  }

  const handleStop = () => {
    onStop?.()
  }

  return (
    <Group h="100%" px="md" justify="space-between">
      <Group>
        <Title order={4}>GenGlossary</Title>
        <Badge
          color={statusColors[status]}
          data-testid="status-badge"
        >
          {status}
        </Badge>
      </Group>

      <Group>
        <Button
          leftSection={<IconPlayerPlay size={16} />}
          variant="filled"
          color="green"
          onClick={handleRun}
          disabled={status === 'running'}
          aria-label="Run"
        >
          Run
        </Button>
        <Button
          leftSection={<IconPlayerStop size={16} />}
          variant="outline"
          color="red"
          onClick={handleStop}
          disabled={status !== 'running'}
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
