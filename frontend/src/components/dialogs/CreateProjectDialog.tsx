import { useState } from 'react'
import { Modal, TextInput, Button, Stack, Group } from '@mantine/core'
import { useCreateProject } from '../../api/hooks'
import { LlmSettingsForm } from '../inputs/LlmSettingsForm'
import { DEFAULT_OLLAMA_BASE_URL } from '../../constants/llm'

interface CreateProjectDialogProps {
  opened: boolean
  onClose: () => void
}

export function CreateProjectDialog({ opened, onClose }: CreateProjectDialogProps) {
  const [name, setName] = useState('')
  const [llmProvider, setLlmProvider] = useState('ollama')
  const [llmModel, setLlmModel] = useState('')
  const [baseUrl, setBaseUrl] = useState(DEFAULT_OLLAMA_BASE_URL)
  const [errors, setErrors] = useState<{ name?: string }>({})

  const createMutation = useCreateProject()

  const handleSubmit = async () => {
    // Validation
    const newErrors: { name?: string } = {}

    if (!name.trim()) {
      newErrors.name = 'Name is required'
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors)
      return
    }

    setErrors({})

    try {
      const trimmedBaseUrl = baseUrl.trim()
      await createMutation.mutateAsync({
        name: name.trim(),
        llm_provider: llmProvider,
        llm_model: llmModel,
        llm_base_url: trimmedBaseUrl || undefined,
      })
      handleClose()
    } catch (error) {
      console.error('Failed to create project:', error)
    }
  }

  const handleClose = () => {
    setName('')
    setLlmProvider('ollama')
    setLlmModel('')
    setBaseUrl(DEFAULT_OLLAMA_BASE_URL)
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

        <LlmSettingsForm
          provider={llmProvider}
          model={llmModel}
          baseUrl={baseUrl}
          onProviderChange={setLlmProvider}
          onModelChange={setLlmModel}
          onBaseUrlChange={setBaseUrl}
          modelLabel="LLM Model"
        />

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
