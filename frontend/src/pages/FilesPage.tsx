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
} from '@mantine/core'
import { IconPlus, IconTrash, IconFile } from '@tabler/icons-react'
import { useNavigate } from '@tanstack/react-router'
import { useFiles, useDeleteFile } from '../api/hooks'
import { AddFileDialog } from '../components/dialogs/AddFileDialog'
import { PageContainer } from '../components/common/PageContainer'

interface FilesPageProps {
  projectId: number
}

export function FilesPage({ projectId }: FilesPageProps) {
  const navigate = useNavigate()
  const { data: files, isLoading, error } = useFiles(projectId)
  const deleteFileMutation = useDeleteFile(projectId)
  const [deletingFileId, setDeletingFileId] = useState<number | null>(null)
  const [addDialogOpened, setAddDialogOpened] = useState(false)

  const handleDeleteFile = async (fileId: number) => {
    setDeletingFileId(fileId)
    try {
      await deleteFileMutation.mutateAsync(fileId)
    } catch (err) {
      console.error('Delete failed:', err)
    } finally {
      setDeletingFileId(null)
    }
  }

  const actionBar = (
    <Group justify="space-between" style={{ width: '100%' }}>
      <Title order={2}>Files</Title>
      <Button leftSection={<IconPlus size={16} />} onClick={() => setAddDialogOpened(true)}>Add</Button>
    </Group>
  )

  return (
    <>
      <PageContainer
        isLoading={isLoading}
        isEmpty={!files || files.length === 0}
        emptyMessage="No files registered"
        actionBar={actionBar}
        loadingTestId="files-loading"
        emptyTestId="files-empty"
        error={error ?? null}
        renderLoading={() => (
          <Box p="md" data-testid="files-loading">
            <Skeleton height={40} mb="md" />
            <Skeleton height={200} />
          </Box>
        )}
        renderEmpty={() => (
          <Card withBorder p="xl" data-testid="files-empty">
            <Stack align="center" gap="md">
              <IconFile size={48} color="var(--mantine-color-dimmed)" />
              <Text size="lg" c="dimmed">
                No files registered
              </Text>
              <Text c="dimmed">
                Click Add to upload files to the project.
              </Text>
              <Button
                leftSection={<IconPlus size={16} />}
                onClick={() => setAddDialogOpened(true)}
              >
                Add Files
              </Button>
            </Stack>
          </Card>
        )}
      >
        <Card withBorder>
          <Table highlightOnHover>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>File Name</Table.Th>
                <Table.Th>Content Hash</Table.Th>
                <Table.Th style={{ width: 100 }}>Actions</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {files?.map((file) => (
                <Table.Tr
                  key={file.id}
                  style={{ cursor: 'pointer' }}
                  tabIndex={0}
                  role="button"
                  aria-label={`View ${file.file_name}`}
                  onClick={() => {
                    navigate({
                      to: `/projects/${projectId}/document-viewer`,
                      search: { file: file.id },
                    })
                  }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault()
                      navigate({
                        to: `/projects/${projectId}/document-viewer`,
                        search: { file: file.id },
                      })
                    }
                  }}
                >
                  <Table.Td>
                    <Group gap="xs">
                      <IconFile size={16} />
                      {file.file_name}
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
                      aria-label={`Delete ${file.file_name}`}
                      onClick={(e) => {
                        e.stopPropagation()
                        handleDeleteFile(file.id)
                      }}
                      loading={deletingFileId === file.id}
                    >
                      <IconTrash size={16} />
                    </Button>
                  </Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        </Card>
      </PageContainer>

      <AddFileDialog
        projectId={projectId}
        opened={addDialogOpened}
        onClose={() => setAddDialogOpened(false)}
      />
    </>
  )
}
