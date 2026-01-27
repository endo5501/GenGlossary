import { useState } from 'react'
import {
  Box,
  Button,
  Card,
  Group,
  Skeleton,
  Stack,
  Table,
  Text,
  Title,
  Badge,
  Alert,
} from '@mantine/core'
import { IconPlus, IconTrash, IconRefresh, IconFile, IconCheck } from '@tabler/icons-react'
import { useFiles, useDiffScan, useDeleteFile } from '../api/hooks'
import type { DiffScanResponse } from '../api/types'

interface FilesPageProps {
  projectId: number
}

function DiffScanResults({ results }: { results: DiffScanResponse }) {
  const hasChanges = results.added.length > 0 || results.modified.length > 0 || results.deleted.length > 0

  if (!hasChanges) {
    return (
      <Alert icon={<IconCheck size={16} />} color="green" data-testid="diff-scan-results">
        No changes detected. All files are up to date.
      </Alert>
    )
  }

  return (
    <Card withBorder p="md" data-testid="diff-scan-results">
      <Stack gap="sm">
        <Title order={5}>Scan Results</Title>

        {results.added.length > 0 && (
          <Box>
            <Group gap="xs" mb="xs">
              <Badge color="green" size="sm">Added</Badge>
              <Text size="sm" c="dimmed">({results.added.length} files)</Text>
            </Group>
            <Stack gap={4}>
              {results.added.map((path) => (
                <Text key={path} size="sm" c="green">
                  + {path}
                </Text>
              ))}
            </Stack>
          </Box>
        )}

        {results.modified.length > 0 && (
          <Box>
            <Group gap="xs" mb="xs">
              <Badge color="yellow" size="sm">Modified</Badge>
              <Text size="sm" c="dimmed">({results.modified.length} files)</Text>
            </Group>
            <Stack gap={4}>
              {results.modified.map((path) => (
                <Text key={path} size="sm" c="yellow">
                  ~ {path}
                </Text>
              ))}
            </Stack>
          </Box>
        )}

        {results.deleted.length > 0 && (
          <Box>
            <Group gap="xs" mb="xs">
              <Badge color="red" size="sm">Deleted</Badge>
              <Text size="sm" c="dimmed">({results.deleted.length} files)</Text>
            </Group>
            <Stack gap={4}>
              {results.deleted.map((path) => (
                <Text key={path} size="sm" c="red">
                  - {path}
                </Text>
              ))}
            </Stack>
          </Box>
        )}
      </Stack>
    </Card>
  )
}

export function FilesPage({ projectId }: FilesPageProps) {
  const { data: files, isLoading, error } = useFiles(projectId)
  const diffScanMutation = useDiffScan(projectId)
  const deleteFileMutation = useDeleteFile(projectId)
  const [scanResults, setScanResults] = useState<DiffScanResponse | null>(null)

  const handleScan = async () => {
    try {
      const results = await diffScanMutation.mutateAsync()
      setScanResults(results)
    } catch (err) {
      console.error('Scan failed:', err)
    }
  }

  const handleDeleteFile = async (fileId: number) => {
    try {
      await deleteFileMutation.mutateAsync(fileId)
    } catch (err) {
      console.error('Delete failed:', err)
    }
  }

  if (isLoading) {
    return (
      <Box p="md" data-testid="files-loading">
        <Skeleton height={40} mb="md" />
        <Skeleton height={200} />
      </Box>
    )
  }

  if (error) {
    return (
      <Box p="md" data-testid="files-error">
        <Text c="red">Error loading files: {error.message}</Text>
      </Box>
    )
  }

  const isEmpty = !files || files.length === 0

  return (
    <Box p="md">
      <Group justify="space-between" mb="lg">
        <Title order={2}>Files</Title>
        <Group gap="sm">
          <Button
            variant="outline"
            leftSection={<IconRefresh size={16} />}
            onClick={handleScan}
            loading={diffScanMutation.isPending}
          >
            Scan
          </Button>
          <Button leftSection={<IconPlus size={16} />}>Add</Button>
        </Group>
      </Group>

      {scanResults && (
        <Box mb="lg">
          <DiffScanResults results={scanResults} />
        </Box>
      )}

      {isEmpty ? (
        <Card withBorder p="xl" data-testid="files-empty">
          <Stack align="center" gap="md">
            <IconFile size={48} color="var(--mantine-color-dimmed)" />
            <Text size="lg" c="dimmed">
              No files registered
            </Text>
            <Text c="dimmed">
              Use Scan to detect files in the document root.
            </Text>
            <Button
              leftSection={<IconRefresh size={16} />}
              onClick={handleScan}
              loading={diffScanMutation.isPending}
            >
              Scan for Files
            </Button>
          </Stack>
        </Card>
      ) : (
        <Card withBorder>
          <Table highlightOnHover>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>File Path</Table.Th>
                <Table.Th>Content Hash</Table.Th>
                <Table.Th style={{ width: 100 }}>Actions</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {files.map((file) => (
                <Table.Tr
                  key={file.id}
                  style={{ cursor: 'pointer' }}
                  onClick={() => {
                    // Navigate to document viewer
                    window.location.href = `/projects/${projectId}/document-viewer?file=${file.id}`
                  }}
                >
                  <Table.Td>
                    <Group gap="xs">
                      <IconFile size={16} />
                      {file.file_path}
                    </Group>
                  </Table.Td>
                  <Table.Td>
                    <Text size="sm" c="dimmed" ff="monospace">
                      {file.content_hash.substring(0, 8)}...
                    </Text>
                  </Table.Td>
                  <Table.Td>
                    <Button
                      variant="subtle"
                      color="red"
                      size="xs"
                      onClick={(e) => {
                        e.stopPropagation()
                        handleDeleteFile(file.id)
                      }}
                      loading={deleteFileMutation.isPending}
                    >
                      <IconTrash size={16} />
                    </Button>
                  </Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        </Card>
      )}
    </Box>
  )
}
