import { useState } from 'react'
import { Modal, TextInput, Button, Stack, Group, Select } from '@mantine/core'
import { useCreateProject } from '../../api/hooks'

const LLM_PROVIDERS = [
  { value: 'ollama', label: 'Ollama' },
  { value: 'openai', label: 'OpenAI' },
]

interface CreateProjectDialogProps {
  opened: boolean
  onClose: () => void
}

export function CreateProjectDialog({ opened, onClose }: CreateProjectDialogProps) {
  const [name, setName] = useState('')
  const [docRoot, setDocRoot] = useState('')
  const [llmProvider, setLlmProvider] = useState('ollama')
  const [llmModel, setLlmModel] = useState('')
  const [baseUrl, setBaseUrl] = useState('')
  const [errors, setErrors] = useState<{ name?: string; doc_root?: string }>({})

  const createMutation = useCreateProject()

  const handleSubmit = async () => {
    // Validation
    const newErrors: { name?: string; doc_root?: string } = {}

    if (!name.trim()) {
      newErrors.name = 'Name is required'
    }
    if (!docRoot.trim()) {
      newErrors.doc_root = 'Document root is required'
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors)
      return
    }

    setErrors({})

    try {
      await createMutation.mutateAsync({
        name: name.trim(),
        doc_root: docRoot.trim(),
        llm_provider: llmProvider,
        llm_model: llmModel,
        llm_base_url: llmProvider === 'openai' ? baseUrl : undefined,
      })
      handleClose()
    } catch (error) {
      console.error('Failed to create project:', error)
    }
  }

  const handleClose = () => {
    setName('')
    setDocRoot('')
    setLlmProvider('ollama')
    setLlmModel('')
    setBaseUrl('')
    setErrors({})
    onClose()
  }

  return (
    <Modal opened={opened} onClose={handleClose} title="Create Project" size="md">
      <Stack gap="md">
        <TextInput
          label="Project Name"
          placeholder="My Project"
          value={name}
          onChange={(e) => setName(e.currentTarget.value)}
          error={errors.name}
          required
        />

        <TextInput
          label="Document Root"
          placeholder="/path/to/documents"
          value={docRoot}
          onChange={(e) => setDocRoot(e.currentTarget.value)}
          error={errors.doc_root}
          required
        />

        <Select
          label="LLM Provider"
          data={LLM_PROVIDERS}
          value={llmProvider}
          onChange={(value) => {
            if (value) {
              setLlmProvider(value)
            }
          }}
        />

        <TextInput
          label="LLM Model"
          placeholder="llama3.2"
          value={llmModel}
          onChange={(e) => setLlmModel(e.currentTarget.value)}
        />

        {llmProvider === 'openai' && (
          <TextInput
            label="Base URL"
            placeholder="https://api.openai.com/v1"
            value={baseUrl}
            onChange={(e) => setBaseUrl(e.currentTarget.value)}
            description="Custom API endpoint for OpenAI-compatible providers"
          />
        )}

        <Group justify="flex-end" gap="sm">
          <Button variant="default" onClick={handleClose}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} loading={createMutation.isPending}>
            Create
          </Button>
        </Group>
      </Stack>
    </Modal>
  )
}
