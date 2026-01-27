import {
  Box,
  Button,
  Group,
  Table,
  Badge,
  Text,
  Paper,
  Stack,
  Loader,
  Center,
  TextInput,
  Modal,
  ActionIcon,
} from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import { IconPlus, IconRefresh, IconTrash } from '@tabler/icons-react'
import { useState } from 'react'
import { useTerms, useCreateTerm, useDeleteTerm, useExtractTerms, useCurrentRun } from '../api/hooks'
import type { TermDetailResponse } from '../api/types'

interface TermsPageProps {
  projectId: number
}

export function TermsPage({ projectId }: TermsPageProps) {
  const { data: terms, isLoading } = useTerms(projectId)
  const { data: currentRun } = useCurrentRun(projectId)
  const [selectedTerm, setSelectedTerm] = useState<TermDetailResponse | null>(null)
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
        if (selectedTerm?.id === termId) {
          setSelectedTerm(null)
        }
      },
    })
  }

  if (isLoading) {
    return (
      <Center data-testid="terms-loading" h={200}>
        <Loader />
      </Center>
    )
  }

  if (!terms || terms.length === 0) {
    return (
      <Stack>
        <Group>
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
        </Group>
        <Center data-testid="terms-empty" h={200}>
          <Text c="dimmed">No terms found. Extract terms from documents or add manually.</Text>
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
      </Group>

      {/* Terms table */}
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
            {terms.map((term) => (
              <Table.Tr
                key={term.id}
                onClick={() => setSelectedTerm(term)}
                style={{ cursor: 'pointer' }}
                bg={selectedTerm?.id === term.id ? 'var(--mantine-color-blue-light)' : undefined}
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

      {/* Detail panel */}
      {selectedTerm && (
        <Paper data-testid="term-detail-panel" withBorder p="md">
          <Group justify="space-between" mb="md">
            <Text fw={600} size="lg">
              {selectedTerm.term_text}
            </Text>
            <Group>
              <ActionIcon
                variant="subtle"
                color="red"
                onClick={() => handleDeleteTerm(selectedTerm.id)}
                aria-label="Delete term"
              >
                <IconTrash size={16} />
              </ActionIcon>
            </Group>
          </Group>

          {selectedTerm.category && (
            <Badge variant="light" mb="md">
              {selectedTerm.category}
            </Badge>
          )}

          <Text fw={500} mb="xs">
            Occurrences ({selectedTerm.occurrences.length})
          </Text>
          <Stack gap="xs">
            {selectedTerm.occurrences.map((occ, idx) => (
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

      {/* Add term modal */}
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
    </Stack>
  )
}
