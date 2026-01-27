import {
  Box,
  Button,
  Group,
  Text,
  Paper,
  Stack,
  Loader,
  Center,
} from '@mantine/core'
import { IconRefresh, IconDownload } from '@tabler/icons-react'
import { useState } from 'react'
import {
  useRefined,
  useExportMarkdown,
  useRegenerateRefined,
  useCurrentRun,
} from '../api/hooks'
import type { GlossaryTermResponse } from '../api/types'

interface RefinedPageProps {
  projectId: number
}

export function RefinedPage({ projectId }: RefinedPageProps) {
  const { data: entries, isLoading } = useRefined(projectId)
  const { data: currentRun } = useCurrentRun(projectId)
  const [selectedEntry, setSelectedEntry] = useState<GlossaryTermResponse | null>(null)

  const exportMarkdown = useExportMarkdown(projectId)
  const regenerateRefined = useRegenerateRefined(projectId)

  const isRunning = currentRun?.status === 'running'

  if (isLoading) {
    return (
      <Center data-testid="refined-loading" h={200}>
        <Loader />
      </Center>
    )
  }

  if (!entries || entries.length === 0) {
    return (
      <Stack>
        <Group>
          <Button
            leftSection={<IconRefresh size={16} />}
            onClick={() => regenerateRefined.mutate()}
            disabled={isRunning}
            aria-label="Regenerate refined glossary"
          >
            Regenerate
          </Button>
          <Button
            leftSection={<IconDownload size={16} />}
            onClick={() => exportMarkdown.mutate()}
            variant="outline"
            disabled={isRunning}
            aria-label="Export as Markdown"
          >
            Export
          </Button>
        </Group>
        <Center data-testid="refined-empty" h={200}>
          <Text c="dimmed">
            No refined glossary entries. Run the full pipeline to generate.
          </Text>
        </Center>
      </Stack>
    )
  }

  return (
    <Stack>
      {/* Action bar */}
      <Group>
        <Button
          leftSection={<IconRefresh size={16} />}
          onClick={() => regenerateRefined.mutate()}
          disabled={isRunning}
          aria-label="Regenerate refined glossary"
        >
          Regenerate
        </Button>
        <Button
          leftSection={<IconDownload size={16} />}
          onClick={() => exportMarkdown.mutate()}
          variant="outline"
          loading={exportMarkdown.isPending}
          aria-label="Export as Markdown"
        >
          Export
        </Button>
      </Group>

      {/* Entries list */}
      <Box style={{ flex: 1 }}>
        <Stack gap="sm">
          {entries.map((entry) => (
            <Paper
              key={entry.id}
              withBorder
              p="md"
              onClick={() => setSelectedEntry(entry)}
              style={{ cursor: 'pointer' }}
              bg={
                selectedEntry?.id === entry.id
                  ? 'var(--mantine-color-blue-light)'
                  : undefined
              }
            >
              <Text fw={600} mb="xs">
                {entry.term_name}
              </Text>
              <Text size="sm" lineClamp={2}>
                {entry.definition}
              </Text>
            </Paper>
          ))}
        </Stack>
      </Box>

      {/* Detail panel */}
      {selectedEntry && (
        <Paper data-testid="refined-detail-panel" withBorder p="md">
          <Text fw={600} size="lg" mb="md">
            {selectedEntry.term_name}
          </Text>

          <Text fw={500} mb="xs">
            Definition
          </Text>
          <Text mb="md">{selectedEntry.definition}</Text>

          <Text fw={500} mb="xs">
            Occurrences ({selectedEntry.occurrences.length})
          </Text>
          <Stack gap="xs">
            {selectedEntry.occurrences.map((occ, idx) => (
              <Paper key={idx} withBorder p="xs">
                <Text size="sm" c="dimmed">
                  {occ.document_path}:{occ.line_number}
                </Text>
                <Text size="sm">{occ.context}</Text>
              </Paper>
            ))}
          </Stack>
        </Paper>
      )}
    </Stack>
  )
}
