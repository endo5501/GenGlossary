import {
  Box,
  Button,
  Text,
  Paper,
  Stack,
} from '@mantine/core'
import { IconRefresh, IconDownload } from '@tabler/icons-react'
import { useState } from 'react'
import {
  useRefined,
  useExportMarkdown,
  useRegenerateRefined,
  useCurrentRun,
} from '../api/hooks'
import { PageContainer } from '../components/common/PageContainer'
import { OccurrenceList } from '../components/common/OccurrenceList'

interface RefinedPageProps {
  projectId: number
}

export function RefinedPage({ projectId }: RefinedPageProps) {
  const { data: entries, isLoading } = useRefined(projectId)
  const { data: currentRun } = useCurrentRun(projectId)
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const selectedEntry = entries?.find((e) => e.id === selectedId) ?? null

  const exportMarkdown = useExportMarkdown(projectId)
  const regenerateRefined = useRegenerateRefined(projectId)

  const isRunning = currentRun?.status === 'running'

  const actionBar = (
    <>
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
    </>
  )

  return (
    <PageContainer
      isLoading={isLoading}
      isEmpty={!entries || entries.length === 0}
      emptyMessage="No refined glossary entries. Run the full pipeline to generate."
      actionBar={actionBar}
      loadingTestId="refined-loading"
      emptyTestId="refined-empty"
    >
      <Box style={{ flex: 1 }}>
        <Stack gap="sm">
          {entries?.map((entry) => (
            <Paper
              key={entry.id}
              withBorder
              p="md"
              onClick={() => setSelectedId(entry.id)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault()
                  setSelectedId(entry.id)
                }
              }}
              tabIndex={0}
              role="button"
              aria-selected={selectedId === entry.id}
              style={{ cursor: 'pointer' }}
              bg={
                selectedId === entry.id
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
          <OccurrenceList occurrences={selectedEntry.occurrences} />
        </Paper>
      )}
    </PageContainer>
  )
}
