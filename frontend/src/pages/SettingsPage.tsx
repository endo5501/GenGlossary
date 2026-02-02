import { useState, useMemo, useEffect } from 'react'
import {
  Box,
  Button,
  Card,
  Center,
  Group,
  Loader,
  Stack,
  Text,
  TextInput,
  Title,
} from '@mantine/core'
import { notifications } from '@mantine/notifications'
import { useProject, useUpdateProject } from '../api/hooks/useProjects'
import { ApiError } from '../api/client'
import { LlmSettingsForm } from '../components/inputs/LlmSettingsForm'
import { DEFAULT_OLLAMA_BASE_URL } from '../constants/llm'

interface SettingsPageProps {
  projectId: number
}

export function SettingsPage({ projectId }: SettingsPageProps) {
  const { data: project, isLoading, error } = useProject(projectId)
  const updateMutation = useUpdateProject()

  // Form state
  const [name, setName] = useState<string>('')
  const [provider, setProvider] = useState<string>('ollama')
  const [model, setModel] = useState<string>('')
  const [baseUrl, setBaseUrl] = useState<string>('')
  const [nameError, setNameError] = useState<string>('')

  // Initialize form when project loads or projectId changes
  useEffect(() => {
    if (project) {
      setName(project.name)
      setProvider(project.llm_provider)
      setModel(project.llm_model)
      // Use default URL for Ollama if not set
      setBaseUrl(
        project.llm_base_url ||
          (project.llm_provider === 'ollama' ? DEFAULT_OLLAMA_BASE_URL : '')
      )
      setNameError('')
    }
  }, [project, projectId])

  // Check if there are changes
  const hasChanges = useMemo(() => {
    if (!project) return false
    // For base URL comparison, treat empty string and default Ollama URL as equivalent
    // when provider is Ollama
    const effectiveProjectBaseUrl =
      project.llm_base_url ||
      (project.llm_provider === 'ollama' ? DEFAULT_OLLAMA_BASE_URL : '')
    const effectiveBaseUrl =
      baseUrl || (provider === 'ollama' ? DEFAULT_OLLAMA_BASE_URL : '')

    return (
      name !== project.name ||
      provider !== project.llm_provider ||
      model !== project.llm_model ||
      effectiveBaseUrl !== effectiveProjectBaseUrl
    )
  }, [project, name, provider, model, baseUrl])

  const getErrorMessage = (err: unknown): string => {
    if (err instanceof ApiError) {
      return err.detail || err.message
    }
    if (err instanceof Error) {
      return err.message
    }
    return 'Failed to save settings'
  }

  const handleSave = async () => {
    if (!name.trim()) {
      setNameError('Name is required')
      return
    }
    setNameError('')

    try {
      await updateMutation.mutateAsync({
        id: projectId,
        data: { name, llm_provider: provider, llm_model: model, llm_base_url: baseUrl },
      })

      notifications.show({
        title: 'Settings saved',
        message: 'Project settings have been updated successfully.',
        color: 'green',
      })
    } catch (err) {
      const errorMessage = getErrorMessage(err)
      const title = errorMessage.includes('already exists')
        ? `Project name already exists: ${name}`
        : errorMessage

      notifications.show({
        title: 'Error',
        message: title,
        color: 'red',
      })
    }
  }

  if (isLoading) {
    return (
      <Center h="100%" data-testid="settings-loading">
        <Loader size="lg" />
      </Center>
    )
  }

  if (error) {
    const errorMessage =
      error instanceof ApiError && error.status === 404
        ? 'Project not found'
        : 'Failed to load project settings'
    return (
      <Center h="100%" data-testid="settings-error">
        <Text c="red">{errorMessage}</Text>
      </Center>
    )
  }

  if (!project) {
    return null
  }

  return (
    <Box p="md">
      <Stack gap="lg">
        <Title order={2}>Settings</Title>

        <Card withBorder shadow="sm" radius="md" p="lg" data-testid="settings-form">
          <Stack gap="md">
            <Title order={4}>Project Settings</Title>

            <TextInput
              label="Project Name"
              placeholder="Enter project name"
              value={name}
              onChange={(e) => {
                const newValue = e.currentTarget.value
                setName(newValue)
                if (newValue.trim() && nameError) {
                  setNameError('')
                }
              }}
              error={nameError}
              required
            />

            <TextInput
              label="Document Root"
              value={project.doc_root}
              disabled
              description="Document root cannot be changed after project creation"
            />

            <Title order={4} mt="md">
              LLM Settings
            </Title>

            <LlmSettingsForm
              provider={provider}
              model={model}
              baseUrl={baseUrl}
              onProviderChange={setProvider}
              onModelChange={setModel}
              onBaseUrlChange={setBaseUrl}
            />

            <Group justify="flex-end" mt="md">
              <Button
                onClick={handleSave}
                loading={updateMutation.isPending}
                disabled={!hasChanges || updateMutation.isPending}
              >
                Save
              </Button>
            </Group>
          </Stack>
        </Card>
      </Stack>
    </Box>
  )
}
