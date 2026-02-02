import { useState } from 'react'
import { Modal, TextInput, Button, Stack, Group, Select, Alert, Loader } from '@mantine/core'
import { IconAlertCircle } from '@tabler/icons-react'
import { useCreateProject } from '../../api/hooks'
import { useOllamaModels } from '../../api/hooks/useOllamaModels'

const LLM_PROVIDERS = [
  { value: 'ollama', label: 'Ollama' },
  { value: 'openai', label: 'OpenAI' },
]

const DEFAULT_OLLAMA_BASE_URL = 'http://localhost:11434'

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

  // Fetch Ollama models when provider is ollama
  const ollamaBaseUrl = llmProvider === 'ollama' ? baseUrl : ''
  const {
    models: ollamaModels,
    isLoading: isLoadingModels,
    error: ollamaError,
  } = useOllamaModels(ollamaBaseUrl)

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

        <Select
          label="LLM Provider"
          data={LLM_PROVIDERS}
          value={llmProvider}
          onChange={(value) => {
            if (value) {
              setLlmProvider(value)
              // Set default base URL when switching providers
              if (value === 'ollama') {
                setBaseUrl(DEFAULT_OLLAMA_BASE_URL)
              } else {
                setBaseUrl('')
              }
            }
          }}
        />

        <TextInput
          label="Base URL"
          placeholder={
            llmProvider === 'ollama'
              ? DEFAULT_OLLAMA_BASE_URL
              : 'https://api.openai.com/v1'
          }
          value={baseUrl}
          onChange={(e) => setBaseUrl(e.currentTarget.value)}
          description={
            llmProvider === 'ollama'
              ? 'Ollama server URL'
              : 'Custom API endpoint for OpenAI-compatible providers'
          }
        />

        {llmProvider === 'ollama' && ollamaError && (
          <Alert
            icon={<IconAlertCircle size={16} />}
            color="yellow"
            title="Ollamaサーバーに接続できません"
          >
            モデル名を手動で入力してください
          </Alert>
        )}

        {llmProvider === 'ollama' && !ollamaError && ollamaModels.length > 0 ? (
          <Select
            label="LLM Model"
            placeholder="Select a model"
            data={ollamaModels.map((m) => ({ value: m, label: m }))}
            value={llmModel}
            onChange={(value) => setLlmModel(value || '')}
            searchable
            disabled={isLoadingModels}
            rightSection={isLoadingModels ? <Loader size="xs" /> : undefined}
          />
        ) : (
          <TextInput
            label="LLM Model"
            placeholder={llmProvider === 'ollama' ? 'e.g., llama3.2' : 'e.g., gpt-4'}
            value={llmModel}
            onChange={(e) => setLlmModel(e.currentTarget.value)}
            disabled={llmProvider === 'ollama' && isLoadingModels && !ollamaError}
            rightSection={
              llmProvider === 'ollama' && isLoadingModels && !ollamaError ? (
                <Loader size="xs" />
              ) : undefined
            }
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
