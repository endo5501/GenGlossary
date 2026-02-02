import {
  Paper,
  Text,
  Title,
  Stack,
  Group,
  Button,
  Badge,
  Divider,
} from '@mantine/core'
import { IconTrash, IconEdit, IconArrowRight } from '@tabler/icons-react'
import type { GlossaryTermResponse } from '../../api/types'
import { OccurrenceList } from '../common/OccurrenceList'

interface TermCardProps {
  selectedTerm: string | null
  refinedData: GlossaryTermResponse | null
  provisionalData: GlossaryTermResponse | null
}

export function TermCard({
  selectedTerm,
  refinedData,
  provisionalData,
}: TermCardProps) {
  if (!selectedTerm) {
    return (
      <Paper withBorder p="xl" h="100%" style={{ position: 'sticky', top: 0 }}>
        <Stack align="center" justify="center" h="100%">
          <Text c="dimmed">Click a term in the document to view details</Text>
        </Stack>
      </Paper>
    )
  }

  // Use refined data if available, otherwise fallback to provisional
  const termData = refinedData ?? provisionalData
  const dataSource = refinedData ? 'refined' : provisionalData ? 'provisional' : null

  if (!termData) {
    return (
      <Paper withBorder p="xl" h="100%" style={{ position: 'sticky', top: 0 }}>
        <Stack>
          <Title order={4}>{selectedTerm}</Title>
          <Badge color="gray">Not defined</Badge>
          <Text c="dimmed">
            This term has no definition yet. Run the glossary generation to
            create definitions.
          </Text>
        </Stack>
      </Paper>
    )
  }

  return (
    <Paper withBorder p="md" h="100%" style={{ position: 'sticky', top: 0 }}>
      <Stack gap="md">
        <Group justify="space-between">
          <Title order={4}>{termData.term_name}</Title>
          <Badge color={dataSource === 'refined' ? 'green' : 'yellow'}>
            {dataSource === 'refined' ? 'Refined' : 'Provisional'}
          </Badge>
        </Group>

        <Divider />

        <Stack gap="xs">
          <Text fw={500} size="sm">
            Definition
          </Text>
          <Text>{termData.definition}</Text>
        </Stack>

        {termData.occurrences && termData.occurrences.length > 0 && (
          <>
            <Divider />
            <Stack gap="xs">
              <Text fw={500} size="sm">
                Occurrences ({termData.occurrences.length})
              </Text>
              <OccurrenceList occurrences={termData.occurrences} />
            </Stack>
          </>
        )}

        <Divider />

        <Group gap="xs">
          <Button
            variant="light"
            size="xs"
            leftSection={<IconTrash size={14} />}
            disabled
          >
            Exclude
          </Button>
          <Button
            variant="light"
            size="xs"
            leftSection={<IconEdit size={14} />}
            disabled
          >
            Edit
          </Button>
          <Button
            variant="light"
            size="xs"
            leftSection={<IconArrowRight size={14} />}
            disabled
          >
            Jump
          </Button>
        </Group>
      </Stack>
    </Paper>
  )
}
