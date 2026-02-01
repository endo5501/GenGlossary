import { useState, useEffect } from 'react'
import {
  Modal,
  Button,
  Stack,
  Group,
  Text,
  List,
  ActionIcon,
  Alert,
} from '@mantine/core'
import { Dropzone } from '@mantine/dropzone'
import {
  IconUpload,
  IconX,
  IconFile,
  IconAlertCircle,
} from '@tabler/icons-react'
import { useCreateFilesBulk } from '../../api/hooks'
import type { FileCreateRequest } from '../../api/types'

interface SelectedFile {
  name: string
  content: string
}

interface AddFileDialogProps {
  projectId: number
  opened: boolean
  onClose: () => void
}

const ALLOWED_EXTENSIONS = ['.txt', '.md']
const MAX_FILE_SIZE = 5 * 1024 * 1024 // 5MB

export function AddFileDialog({ projectId, opened, onClose }: AddFileDialogProps) {
  const [selectedFiles, setSelectedFiles] = useState<SelectedFile[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const createMutation = useCreateFilesBulk(projectId)

  // Reset form when dialog opens
  useEffect(() => {
    if (opened) {
      setSelectedFiles([])
      setError(null)
    }
  }, [opened])

  const handleDrop = async (files: File[]) => {
    setError(null)
    setLoading(true)

    try {
      const newFiles: SelectedFile[] = []

      for (const file of files) {
        // Check extension
        const ext = '.' + file.name.split('.').pop()?.toLowerCase()
        if (!ALLOWED_EXTENSIONS.includes(ext)) {
          setError(`Invalid file extension: ${file.name}. Only .txt and .md files are allowed.`)
          continue
        }

        // Check if already selected
        if (selectedFiles.some((f) => f.name === file.name) || newFiles.some((f) => f.name === file.name)) {
          setError(`Duplicate file: ${file.name}`)
          continue
        }

        // Read file content
        const content = await readFileContent(file)
        newFiles.push({ name: file.name, content })
      }

      setSelectedFiles((prev) => [...prev, ...newFiles])
    } catch (err) {
      console.error('Failed to read files:', err)
      setError('Failed to read files. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const readFileContent = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = () => resolve(reader.result as string)
      reader.onerror = () => reject(reader.error)
      reader.readAsText(file)
    })
  }

  const handleRemoveFile = (fileName: string) => {
    setSelectedFiles((prev) => prev.filter((f) => f.name !== fileName))
    setError(null)
  }

  const handleSubmit = async () => {
    if (selectedFiles.length === 0) {
      setError('Please select at least one file')
      return
    }

    setError(null)

    try {
      const files: FileCreateRequest[] = selectedFiles.map((f) => ({
        file_name: f.name,
        content: f.content,
      }))
      await createMutation.mutateAsync(files)
      handleClose()
    } catch (err: unknown) {
      console.error('Failed to add files:', err)
      const errorDetail = (err as { detail?: string })?.detail
      setError(errorDetail || 'Failed to add files. Please try again.')
    }
  }

  const handleClose = () => {
    setSelectedFiles([])
    setError(null)
    onClose()
  }

  return (
    <Modal opened={opened} onClose={handleClose} title="Add Files" size="lg">
      <Stack gap="md">
        <Dropzone
          onDrop={handleDrop}
          maxSize={MAX_FILE_SIZE}
          accept={['text/markdown', 'text/plain']}
          loading={loading}
          useFsAccessApi={false}
        >
          <Group justify="center" gap="xl" mih={120} style={{ pointerEvents: 'none' }}>
            <Dropzone.Accept>
              <IconUpload size={50} stroke={1.5} />
            </Dropzone.Accept>
            <Dropzone.Reject>
              <IconX size={50} stroke={1.5} />
            </Dropzone.Reject>
            <Dropzone.Idle>
              <IconFile size={50} stroke={1.5} />
            </Dropzone.Idle>

            <div>
              <Text size="lg" inline>
                Drag files here or click to select
              </Text>
              <Text size="sm" c="dimmed" inline mt={7}>
                Only .txt and .md files are allowed (max 5MB each)
              </Text>
            </div>
          </Group>
        </Dropzone>

        {error && (
          <Alert icon={<IconAlertCircle size={16} />} color="red" variant="light">
            {error}
          </Alert>
        )}

        {selectedFiles.length > 0 && (
          <Stack gap="xs">
            <Text fw={500}>Selected Files ({selectedFiles.length})</Text>
            <List spacing="xs" size="sm">
              {selectedFiles.map((file) => (
                <List.Item
                  key={file.name}
                  icon={
                    <ActionIcon
                      color="red"
                      variant="subtle"
                      size="sm"
                      onClick={() => handleRemoveFile(file.name)}
                    >
                      <IconX size={14} />
                    </ActionIcon>
                  }
                >
                  {file.name}
                </List.Item>
              ))}
            </List>
          </Stack>
        )}

        <Group justify="flex-end" gap="sm">
          <Button variant="default" onClick={handleClose} type="button">
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            loading={createMutation.isPending}
            disabled={selectedFiles.length === 0}
          >
            Add ({selectedFiles.length})
          </Button>
        </Group>
      </Stack>
    </Modal>
  )
}
