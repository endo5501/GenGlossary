import { Select, TextInput, Alert, Loader, type ComboboxProps } from '@mantine/core'
import { IconAlertCircle } from '@tabler/icons-react'
import { useOllamaModels } from '../../api/hooks/useOllamaModels'
import { DEFAULT_OLLAMA_BASE_URL, LLM_PROVIDERS } from '../../constants/llm'

interface LlmSettingsFormProps {
  provider: string
  model: string
  baseUrl: string
  onProviderChange: (provider: string) => void
  onModelChange: (model: string) => void
  onBaseUrlChange: (baseUrl: string) => void
  modelLabel?: string
  /** For testing purposes - pass { withinPortal: false } to disable portal */
  comboboxProps?: ComboboxProps
}

export function LlmSettingsForm({
  provider,
  model,
  baseUrl,
  onProviderChange,
  onModelChange,
  onBaseUrlChange,
  modelLabel = 'Model',
  comboboxProps,
}: LlmSettingsFormProps) {
  const ollamaBaseUrl = provider === 'ollama' ? baseUrl : ''
  const {
    models: ollamaModels,
    isLoading: isLoadingModels,
    error: ollamaError,
  } = useOllamaModels(ollamaBaseUrl)

  const handleProviderChange = (value: string | null) => {
    if (value) {
      onProviderChange(value)
      // Set default base URL when switching providers
      if (value === 'ollama') {
        onBaseUrlChange(DEFAULT_OLLAMA_BASE_URL)
      } else {
        onBaseUrlChange('')
      }
    }
  }

  const showModelSelect =
    provider === 'ollama' && !ollamaError && ollamaModels.length > 0

  return (
    <>
      <Select
        label="Provider"
        data={LLM_PROVIDERS.map((p) => ({ value: p.value, label: p.label }))}
        value={provider}
        onChange={handleProviderChange}
        comboboxProps={comboboxProps}
      />

      <TextInput
        label="Base URL"
        placeholder={
          provider === 'ollama'
            ? DEFAULT_OLLAMA_BASE_URL
            : 'https://api.openai.com/v1'
        }
        value={baseUrl}
        onChange={(e) => onBaseUrlChange(e.currentTarget.value)}
        description={
          provider === 'ollama'
            ? 'Ollama server URL'
            : 'Custom API endpoint for OpenAI-compatible providers'
        }
      />

      {provider === 'ollama' && ollamaError && (
        <Alert
          icon={<IconAlertCircle size={16} />}
          color="yellow"
          title="Ollamaサーバーに接続できません"
        >
          モデル名を手動で入力してください
        </Alert>
      )}

      {showModelSelect ? (
        <Select
          label={modelLabel}
          placeholder="Select a model"
          data={ollamaModels.map((m) => ({ value: m, label: m }))}
          value={model}
          onChange={(value) => onModelChange(value || '')}
          searchable
          disabled={isLoadingModels}
          rightSection={isLoadingModels ? <Loader size="xs" /> : undefined}
          comboboxProps={comboboxProps}
        />
      ) : (
        <TextInput
          label={modelLabel}
          placeholder={provider === 'ollama' ? 'e.g., llama3.2' : 'e.g., gpt-4'}
          value={model}
          onChange={(e) => onModelChange(e.currentTarget.value)}
          disabled={provider === 'ollama' && isLoadingModels && !ollamaError}
          rightSection={
            provider === 'ollama' && isLoadingModels && !ollamaError ? (
              <Loader size="xs" />
            ) : undefined
          }
        />
      )}
    </>
  )
}
