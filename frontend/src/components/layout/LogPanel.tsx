import { Paper, Text, Group, ActionIcon, Collapse, Box } from '@mantine/core'
import { IconChevronDown, IconChevronUp } from '@tabler/icons-react'
import { useState } from 'react'

export function LogPanel() {
  const [opened, setOpened] = useState(true)

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
          <Text size="xs" c="dimmed">
            Log output will appear here...
          </Text>
        </Box>
      </Collapse>
    </Paper>
  )
}
