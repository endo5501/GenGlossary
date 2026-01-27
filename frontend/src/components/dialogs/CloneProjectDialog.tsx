import { useState, useEffect } from 'react'
import { Modal, TextInput, Button, Stack, Group, Text } from '@mantine/core'
import { useCloneProject } from '../../api/hooks'
import type { ProjectResponse } from '../../api/types'

interface CloneProjectDialogProps {
  opened: boolean
  onClose: () => void
  project: ProjectResponse
}

export function CloneProjectDialog({
  opened,
  onClose,
  project,
}: CloneProjectDialogProps) {
  const [newName, setNewName] = useState(`${project.name} (Copy)`)
  const [error, setError] = useState<string | null>(null)

  // Reset state when dialog opens or project changes
  useEffect(() => {
    if (opened) {
      setNewName(`${project.name} (Copy)`)
      setError(null)
    }
  }, [opened, project.id])

  const cloneMutation = useCloneProject()

  const handleSubmit = async () => {
    if (!newName.trim()) {
      setError('Name is required')
      return
    }

    setError(null)

    try {
      await cloneMutation.mutateAsync({
        id: project.id,
        data: { new_name: newName.trim() },
      })
      handleClose()
    } catch (err) {
      console.error('Failed to clone project:', err)
      setError('Failed to clone project')
    }
  }

  const handleClose = () => {
    setNewName(`${project.name} (Copy)`)
    setError(null)
    onClose()
  }

  return (
    <Modal opened={opened} onClose={handleClose} title="Clone Project" size="md">
      <Stack gap="md">
        <Text size="sm" c="dimmed">
          Create a copy of <strong>{project.name}</strong> with a new name.
          The document root and settings will be copied.
        </Text>

        <TextInput
          label="New Project Name"
          placeholder="Project name"
          value={newName}
          onChange={(e) => setNewName(e.currentTarget.value)}
          error={error}
          required
        />

        <Group justify="flex-end" gap="sm">
          <Button variant="default" onClick={handleClose}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} loading={cloneMutation.isPending}>
            Clone
          </Button>
        </Group>
      </Stack>
    </Modal>
  )
}
