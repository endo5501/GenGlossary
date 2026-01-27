import {
  Box,
  Button,
  Group,
  Table,
  Badge,
  Text,
  Paper,
  Stack,
  TextInput,
  Modal,
  ActionIcon,
} from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import { IconPlus, IconRefresh, IconTrash } from '@tabler/icons-react'
import { useState } from 'react'
import { useTerms, useCreateTerm, useDeleteTerm, useExtractTerms, useCurrentRun } from '../api/hooks'
import { PageContainer } from '../components/common/PageContainer'
import { OccurrenceList } from '../components/common/OccurrenceList'

interface TermsPageProps {
  projectId: number
}

export function TermsPage({ projectId }: TermsPageProps) {
  const { data: terms, isLoading } = useTerms(projectId)
  const { data: currentRun } = useCurrentRun(projectId)
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const selectedTerm = terms?.find((t) => t.id === selectedId) ?? null
  const [opened, { open, close }] = useDisclosure(false)
  const [newTermText, setNewTermText] = useState('')
  const [newTermCategory, setNewTermCategory] = useState('')

  const createTerm = useCreateTerm(projectId)
  const deleteTerm = useDeleteTerm(projectId)
  const extractTerms = useExtractTerms(projectId)

  const isRunning = currentRun?.status === 'running'

  const handleAddTerm = () => {
    if (!newTermText.trim()) return
    createTerm.mutate(
      { term_text: newTermText.trim(), category: newTermCategory.trim() || undefined },
      {
        onSuccess: () => {
          setNewTermText('')
          setNewTermCategory('')
          close()
        },
      }
    )
  }

  const handleDeleteTerm = (termId: number) => {
    deleteTerm.mutate(termId, {
      onSuccess: () => {
        if (selectedId === termId) {
          setSelectedId(null)
        }
      },
    })
  }

  const actionBar = (
    <>
      <Button
        leftSection={<IconRefresh size={16} />}
        onClick={() => extractTerms.mutate()}
        disabled={isRunning}
        aria-label="Extract terms"
      >
        Extract
      </Button>
      <Button
        leftSection={<IconPlus size={16} />}
        onClick={open}
        disabled={isRunning}
        aria-label="Add term"
      >
        Add
      </Button>
    </>
  )

  return (
    <PageContainer
      isLoading={isLoading}
      isEmpty={!terms || terms.length === 0}
      emptyMessage="No terms found. Extract terms from documents or add manually."
      actionBar={actionBar}
      loadingTestId="terms-loading"
      emptyTestId="terms-empty"
    >
      <Box style={{ flex: 1 }}>
        <Table highlightOnHover>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Term</Table.Th>
              <Table.Th>Category</Table.Th>
              <Table.Th>Occurrences</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {terms?.map((term) => (
              <Table.Tr
                key={term.id}
                onClick={() => setSelectedId(term.id)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault()
                    setSelectedId(term.id)
                  }
                }}
                tabIndex={0}
                role="button"
                aria-selected={selectedId === term.id}
                style={{ cursor: 'pointer' }}
                bg={selectedId === term.id ? 'var(--mantine-color-blue-light)' : undefined}
              >
                <Table.Td>{term.term_text}</Table.Td>
                <Table.Td>
                  {term.category ? (
                    <Badge variant="light">{term.category}</Badge>
                  ) : (
                    <Text c="dimmed" size="sm">
                      -
                    </Text>
                  )}
                </Table.Td>
                <Table.Td>{term.occurrences.length}</Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
      </Box>

      {selectedTerm && (
        <Paper data-testid="term-detail-panel" withBorder p="md">
          <Group justify="space-between" mb="md">
            <Text fw={600} size="lg">
              {selectedTerm.term_text}
            </Text>
            <ActionIcon
              variant="subtle"
              color="red"
              onClick={() => handleDeleteTerm(selectedTerm.id)}
              aria-label="Delete term"
            >
              <IconTrash size={16} />
            </ActionIcon>
          </Group>

          {selectedTerm.category && (
            <Badge variant="light" mb="md">
              {selectedTerm.category}
            </Badge>
          )}

          <Text fw={500} mb="xs">
            Occurrences ({selectedTerm.occurrences.length})
          </Text>
          <OccurrenceList occurrences={selectedTerm.occurrences} />
        </Paper>
      )}

      <Modal opened={opened} onClose={close} title="Add Term">
        <Stack>
          <TextInput
            label="Term"
            placeholder="Enter term text"
            value={newTermText}
            onChange={(e) => setNewTermText(e.target.value)}
            required
          />
          <TextInput
            label="Category"
            placeholder="Enter category (optional)"
            value={newTermCategory}
            onChange={(e) => setNewTermCategory(e.target.value)}
          />
          <Group justify="flex-end">
            <Button variant="subtle" onClick={close}>
              Cancel
            </Button>
            <Button onClick={handleAddTerm} loading={createTerm.isPending}>
              Add
            </Button>
          </Group>
        </Stack>
      </Modal>
    </PageContainer>
  )
}
