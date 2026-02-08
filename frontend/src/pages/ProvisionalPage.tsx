import {
  Box,
  Button,
  Group,
  Table,
  Text,
  Paper,
  Stack,
  Textarea,
  Slider,
  Progress,
} from '@mantine/core'
import { IconRefresh, IconDeviceFloppy } from '@tabler/icons-react'
import { useState, useEffect } from 'react'
import {
  useProvisional,
  useUpdateProvisional,
  useRegenerateProvisional,
  useCurrentRun,
} from '../api/hooks'
import { PageContainer } from '../components/common/PageContainer'
import { SplitLayout } from '../components/common/SplitLayout'
import { OccurrenceList } from '../components/common/OccurrenceList'
import { getRowSelectionProps } from '../utils/getRowSelectionProps'

interface ProvisionalPageProps {
  projectId: number
}

const getConfidenceColor = (confidence: number) =>
  confidence >= 0.8 ? 'green' : confidence >= 0.5 ? 'yellow' : 'red'

export function ProvisionalPage({ projectId }: ProvisionalPageProps) {
  const { data: entries, isLoading } = useProvisional(projectId)
  const { data: currentRun } = useCurrentRun(projectId)
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const selectedEntry = entries?.find((e) => e.id === selectedId) ?? null
  const [editDefinition, setEditDefinition] = useState('')
  const [editConfidence, setEditConfidence] = useState(0)

  const updateProvisional = useUpdateProvisional(projectId)
  const regenerateProvisional = useRegenerateProvisional(projectId)

  const isRunning = currentRun?.status === 'running'

  useEffect(() => {
    if (selectedEntry) {
      setEditDefinition(selectedEntry.definition)
      setEditConfidence(selectedEntry.confidence)
    }
  }, [selectedEntry])

  const handleSave = () => {
    if (!selectedEntry) return
    updateProvisional.mutate({
      entryId: selectedEntry.id,
      data: {
        definition: editDefinition,
        confidence: editConfidence,
      },
    })
  }

  const actionBar = (
    <Button
      leftSection={<IconRefresh size={16} />}
      onClick={() => regenerateProvisional.mutate()}
      disabled={isRunning}
      aria-label="Regenerate provisional glossary"
    >
      Regenerate
    </Button>
  )

  return (
    <PageContainer
      isLoading={isLoading}
      isEmpty={!entries || entries.length === 0}
      emptyMessage="No provisional glossary entries. Run the pipeline to generate."
      actionBar={actionBar}
      loadingTestId="provisional-loading"
      emptyTestId="provisional-empty"
    >
      <SplitLayout
        list={
          <Box style={{ flex: 1 }}>
            <Table highlightOnHover>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Term</Table.Th>
                  <Table.Th>Definition</Table.Th>
                  <Table.Th>Confidence</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {entries?.map((entry) => (
                  <Table.Tr
                    key={entry.id}
                    {...getRowSelectionProps(entry, selectedId, setSelectedId)}
                  >
                    <Table.Td>{entry.term_name}</Table.Td>
                    <Table.Td>
                      <Text lineClamp={2}>{entry.definition}</Text>
                    </Table.Td>
                    <Table.Td>
                      <Group gap="xs">
                        <Progress
                          value={entry.confidence * 100}
                          size="sm"
                          w={60}
                          color={getConfidenceColor(entry.confidence)}
                        />
                        <Text size="sm">{Math.round(entry.confidence * 100)}%</Text>
                      </Group>
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </Box>
        }
        detail={selectedEntry && (
          <Paper data-testid="provisional-detail-editor" withBorder p="md">
            <Group justify="space-between" mb="md">
              <Text fw={600} size="lg">
                {selectedEntry.term_name}
              </Text>
              <Button
                leftSection={<IconDeviceFloppy size={16} />}
                onClick={handleSave}
                loading={updateProvisional.isPending}
                disabled={isRunning}
              >
                Save
              </Button>
            </Group>

            <Stack gap="md">
              {selectedEntry.aliases.length > 0 && (
                <Box>
                  <Text fw={500} mb="xs">
                    Aliases
                  </Text>
                  <Text size="sm">{selectedEntry.aliases.join('、')}</Text>
                </Box>
              )}

              <Textarea
                label="Definition"
                value={editDefinition}
                onChange={(e) => setEditDefinition(e.target.value)}
                minRows={3}
                disabled={isRunning}
              />

              <Box>
                <Text size="sm" fw={500} mb="xs">
                  Confidence: {Math.round(editConfidence * 100)}%
                </Text>
                <Slider
                  value={editConfidence * 100}
                  onChange={(val) => setEditConfidence(val / 100)}
                  min={0}
                  max={100}
                  step={1}
                  disabled={isRunning}
                />
              </Box>

              <Box>
                <Text fw={500} mb="xs">
                  Occurrences ({selectedEntry.occurrences.length})
                </Text>
                <OccurrenceList occurrences={selectedEntry.occurrences} />
              </Box>
            </Stack>
          </Paper>
        )}
      />
    </PageContainer>
  )
}
