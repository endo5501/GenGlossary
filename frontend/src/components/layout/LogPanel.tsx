import { Paper, Text, Group, ActionIcon, Collapse, Box } from '@mantine/core'
import { IconChevronDown, IconChevronUp } from '@tabler/icons-react'
import { useState, useEffect, useRef } from 'react'
import { useLogStream } from '../../api/hooks'
import type { LogMessage } from '../../api/types'

interface LogPanelProps {
  projectId?: number
  runId?: number
}

const levelColors: Record<LogMessage['level'], string> = {
  info: 'var(--mantine-color-gray-3)',
  warning: 'var(--mantine-color-yellow-5)',
  error: 'var(--mantine-color-red-5)',
}

export function LogPanel({ projectId, runId }: LogPanelProps) {
  const [opened, setOpened] = useState(true)
  const scrollRef = useRef<HTMLDivElement>(null)

  // Use SSE hook when projectId and runId are provided
  const { logs } = useLogStream(projectId ?? 0, runId)

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [logs])

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
                key={idx}
                size="xs"
                style={{ color: levelColors[log.level] }}
              >
                [{log.level.toUpperCase()}] {log.message}
              </Text>
            ))
          )}
        </Box>
      </Collapse>
    </Paper>
  )
}
