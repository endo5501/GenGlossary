import { useState, useEffect } from 'react'
import { Modal, TextInput, Button, Stack, Group } from '@mantine/core'
import { useCreateFile } from '../../api/hooks'

interface AddFileDialogProps {
  projectId: number
  opened: boolean
  onClose: () => void
}

export function AddFileDialog({ projectId, opened, onClose }: AddFileDialogProps) {
  const [filePath, setFilePath] = useState('')
  const [error, setError] = useState<string | null>(null)

  const createMutation = useCreateFile(projectId)

  // Reset form when dialog opens
  useEffect(() => {
    if (opened) {
      setFilePath('')
      setError(null)
    }
  }, [opened])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    // Validation
    if (!filePath.trim()) {
      setError('File path is required')
      return
    }

    setError(null)

    try {
      await createMutation.mutateAsync({ file_path: filePath.trim() })
      handleClose()
    } catch (err) {
      console.error('Failed to add file:', err)
      setError('Failed to add file. Please try again.')
    }
  }

  const handleClose = () => {
    setFilePath('')
    setError(null)
    onClose()
  }

  return (
    <Modal opened={opened} onClose={handleClose} title="Add File" size="md">
      <form onSubmit={handleSubmit}>
        <Stack gap="md">
          <TextInput
            label="File Path"
            placeholder="path/to/file.md"
            value={filePath}
            onChange={(e) => setFilePath(e.currentTarget.value)}
            error={error}
          />

          <Group justify="flex-end" gap="sm">
            <Button variant="default" onClick={handleClose} type="button">
              Cancel
            </Button>
            <Button type="submit" loading={createMutation.isPending}>
              Add
            </Button>
          </Group>
        </Stack>
      </form>
    </Modal>
  )
}
