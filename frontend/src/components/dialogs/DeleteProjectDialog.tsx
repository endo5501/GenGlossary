import { Modal, Button, Stack, Group, Text, Alert } from '@mantine/core'
import { IconAlertTriangle } from '@tabler/icons-react'
import { useDeleteProject } from '../../api/hooks'
import type { ProjectResponse } from '../../api/types'

interface DeleteProjectDialogProps {
  opened: boolean
  onClose: () => void
  project: ProjectResponse
  onDeleted: () => void
}

export function DeleteProjectDialog({
  opened,
  onClose,
  project,
  onDeleted,
}: DeleteProjectDialogProps) {
  const deleteMutation = useDeleteProject()

  const handleDelete = async () => {
    try {
      await deleteMutation.mutateAsync(project.id)
      onDeleted()
      onClose()
    } catch (error) {
      console.error('Failed to delete project:', error)
    }
  }

  return (
    <Modal opened={opened} onClose={onClose} title="Delete Project" size="md">
      <Stack gap="md">
        <Alert icon={<IconAlertTriangle size={16} />} color="red" variant="light">
          Are you sure you want to delete this project? This action cannot be undone.
        </Alert>

        <Text>
          Project: <strong>{project.name}</strong>
        </Text>

        <Text size="sm" c="dimmed">
          Note: This will only remove the project from the registry. The project
          database file will not be deleted from disk.
        </Text>

        <Group justify="flex-end" gap="sm">
          <Button variant="default" onClick={onClose}>
            Cancel
          </Button>
          <Button color="red" onClick={handleDelete} loading={deleteMutation.isPending}>
            Delete
          </Button>
        </Group>
      </Stack>
    </Modal>
  )
}
