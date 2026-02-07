import {
  ActionIcon,
  Badge,
  Box,
  LoadingOverlay,
  Table,
  Text,
  Tooltip,
} from '@mantine/core'
import { IconTrash } from '@tabler/icons-react'

interface TermItem {
  id: number
  term_text: string
  source: string
  created_at: string
}

interface TermListTableProps {
  terms: TermItem[] | undefined
  onDelete: (termId: number) => void
  isLoading: boolean
  isDeletePending: boolean
  showSourceColumn: boolean
  deleteTooltip: string
  deleteAriaLabel: string
}

function SourceBadge({ source }: { source: string }) {
  return (
    <Badge variant="light" color={source === 'auto' ? 'blue' : 'green'}>
      {source === 'auto' ? '自動' : '手動'}
    </Badge>
  )
}

export function TermListTable({
  terms,
  onDelete,
  isLoading,
  isDeletePending,
  showSourceColumn,
  deleteTooltip,
  deleteAriaLabel,
}: TermListTableProps) {
  return (
    <Box style={{ flex: 1, position: 'relative' }}>
      <LoadingOverlay visible={isLoading} />
      <Table highlightOnHover>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Term</Table.Th>
            {showSourceColumn && <Table.Th>Source</Table.Th>}
            <Table.Th>Created At</Table.Th>
            <Table.Th w={80}>Actions</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {terms?.map((term) => (
            <Table.Tr key={term.id}>
              <Table.Td>{term.term_text}</Table.Td>
              {showSourceColumn && (
                <Table.Td>
                  <SourceBadge source={term.source} />
                </Table.Td>
              )}
              <Table.Td>
                <Text size="sm" c="dimmed">
                  {new Date(term.created_at).toLocaleDateString('ja-JP')}
                </Text>
              </Table.Td>
              <Table.Td>
                <Tooltip label={deleteTooltip}>
                  <ActionIcon
                    variant="subtle"
                    color="red"
                    onClick={() => onDelete(term.id)}
                    aria-label={deleteAriaLabel}
                    loading={isDeletePending}
                  >
                    <IconTrash size={16} />
                  </ActionIcon>
                </Tooltip>
              </Table.Td>
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>
    </Box>
  )
}
