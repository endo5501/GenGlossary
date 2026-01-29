import {
  Paper,
  Text,
  Group,
  ActionIcon,
  Collapse,
  Box,
  Progress,
  Stack,
} from '@mantine/core'
import { IconChevronDown, IconChevronUp } from '@tabler/icons-react'
import { useState, useEffect, useRef } from 'react'
import { useLogStream } from '../../api/hooks'
import { useLogStore } from '../../store/logStore'
import { levelColors } from '../../utils/colors'

interface LogPanelProps {
  projectId?: number
  runId?: number
  onRunComplete?: () => void
}

export function LogPanel({ projectId, runId, onRunComplete }: LogPanelProps) {
  const [opened, setOpened] = useState(true)
  const scrollRef = useRef<HTMLDivElement>(null)
  const { logs } = useLogStream(projectId ?? 0, runId, { onComplete: onRunComplete })
  const progress = useLogStore((state) => state.latestProgress)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [logs])

  const progressPercent =
    progress && progress.total > 0
      ? Math.round((progress.current / progress.total) * 100)
      : 0

  return (
    <Paper
      data-testid="log-panel"
      withBorder
      p="xs"
      style={{ position: 'relative' }}
    >
      <Group justify="space-between" mb={opened ? 'xs' : 0}>
        <Text size="sm" fw={500}>
          Logs
        </Text>
        <ActionIcon
          variant="subtle"
          onClick={() => setOpened((o) => !o)}
          aria-label={opened ? 'Collapse logs' : 'Expand logs'}
        >
          {opened ? <IconChevronUp size={16} /> : <IconChevronDown size={16} />}
        </ActionIcon>
      </Group>
      <Collapse in={opened}>
        <Stack gap="xs">
          {progress && (
            <Box>
              <Group justify="space-between" mb={4}>
                <Text size="xs" c="dimmed">
                  {progress.step}: {progress.currentTerm}
                </Text>
                <Text size="xs" c="dimmed">
                  {progress.current}/{progress.total}
                </Text>
              </Group>
              <Progress
                data-testid="progress-bar"
                value={progressPercent}
                size="sm"
                animated
              />
            </Box>
          )}
          <Box
            ref={scrollRef}
            data-testid="log-display"
            style={{
              fontFamily: 'monospace',
              fontSize: '12px',
              backgroundColor: 'var(--mantine-color-dark-9)',
              color: 'var(--mantine-color-gray-3)',
              padding: '8px',
              borderRadius: '4px',
              maxHeight: '150px',
              overflowY: 'auto',
            }}
          >
            {logs.length === 0 ? (
              <Text size="xs" c="dimmed">
                Log output will appear here...
              </Text>
            ) : (
              logs.map((log, idx) => (
                <Text
                  key={`${log.run_id}-${idx}`}
                  size="xs"
                  style={{ color: levelColors[log.level] }}
                >
                  [{log.level.toUpperCase()}] {log.message}
                </Text>
              ))
            )}
          </Box>
        </Stack>
      </Collapse>
    </Paper>
  )
}
