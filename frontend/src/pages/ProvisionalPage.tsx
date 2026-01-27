import {
  Box,
  Button,
  Group,
  Table,
  Text,
  Paper,
  Stack,
  Loader,
  Center,
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
import type { GlossaryTermResponse } from '../api/types'

interface ProvisionalPageProps {
  projectId: number
}

export function ProvisionalPage({ projectId }: ProvisionalPageProps) {
  const { data: entries, isLoading } = useProvisional(projectId)
  const { data: currentRun } = useCurrentRun(projectId)
  const [selectedEntry, setSelectedEntry] = useState<GlossaryTermResponse | null>(null)
  const [editDefinition, setEditDefinition] = useState('')
  const [editConfidence, setEditConfidence] = useState(0)

  const updateProvisional = useUpdateProvisional(projectId)
  const regenerateProvisional = useRegenerateProvisional(projectId)

  const isRunning = currentRun?.status === 'running'

  // Sync edit state when selection changes
  useEffect(() => {
    if (selectedEntry) {
      setEditDefinition(selectedEntry.definition)
      setEditConfidence(selectedEntry.confidence)
    }
  }, [selectedEntry])

  const handleSave = () => {
    if (!selectedEntry) return
    updateProvisional.mutate(
      {
        entryId: selectedEntry.id,
        data: {
          definition: editDefinition,
          confidence: editConfidence,
        },
      },
      {
        onSuccess: (updated) => {
          setSelectedEntry({ ...selectedEntry, ...updated })
        },
      }
    )
  }

  if (isLoading) {
    return (
      <Center data-testid="provisional-loading" h={200}>
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
            onClick={() => regenerateProvisional.mutate()}
            disabled={isRunning}
            aria-label="Regenerate provisional glossary"
          >
            Regenerate
          </Button>
        </Group>
        <Center data-testid="provisional-empty" h={200}>
          <Text c="dimmed">
            No provisional glossary entries. Run the pipeline to generate.
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
          onClick={() => regenerateProvisional.mutate()}
          disabled={isRunning}
          aria-label="Regenerate provisional glossary"
        >
          Regenerate
        </Button>
      </Group>

      {/* Entries table */}
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
            {entries.map((entry) => (
              <Table.Tr
                key={entry.id}
                onClick={() => setSelectedEntry(entry)}
                style={{ cursor: 'pointer' }}
                bg={
                  selectedEntry?.id === entry.id
                    ? 'var(--mantine-color-blue-light)'
                    : undefined
                }
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
                      color={entry.confidence >= 0.8 ? 'green' : entry.confidence >= 0.5 ? 'yellow' : 'red'}
                    />
                    <Text size="sm">{Math.round(entry.confidence * 100)}%</Text>
                  </Group>
                </Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
      </Box>

      {/* Detail editor */}
      {selectedEntry && (
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
            </Box>
          </Stack>
        </Paper>
      )}
    </Stack>
  )
}
