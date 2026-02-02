import { describe, expect, it, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MantineProvider } from '@mantine/core'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { server } from './setup'
import { http, HttpResponse } from 'msw'
import { LlmSettingsForm } from '../components/inputs/LlmSettingsForm'

const BASE_URL = 'http://localhost:8000'

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  })

  return {
    user: userEvent.setup(),
    ...render(
      <QueryClientProvider client={queryClient}>
        <MantineProvider>{ui}</MantineProvider>
      </QueryClientProvider>
    ),
  }
}

describe('LlmSettingsForm', () => {
  const defaultProps = {
    provider: 'ollama',
    model: 'llama3.2',
    baseUrl: 'http://localhost:11434',
    onProviderChange: vi.fn(),
    onModelChange: vi.fn(),
    onBaseUrlChange: vi.fn(),
    comboboxProps: { withinPortal: false },
  }

  beforeEach(() => {
    vi.clearAllMocks()
    // Default: Ollama models available
    server.use(
      http.get(`${BASE_URL}/api/ollama/models`, () => {
        return HttpResponse.json({
          models: [
            { name: 'llama2' },
            { name: 'llama3.2' },
            { name: 'codellama' },
          ],
        })
      })
    )
  })

  it('renders provider select', () => {
    renderWithProviders(<LlmSettingsForm {...defaultProps} />)

    const providerInput = screen.getByRole('textbox', { name: /provider/i })
    expect(providerInput).toBeInTheDocument()
    expect(providerInput).toHaveValue('Ollama')
  })

  it('renders base URL input', () => {
    renderWithProviders(<LlmSettingsForm {...defaultProps} />)

    const baseUrlInput = screen.getByLabelText(/base url/i)
    expect(baseUrlInput).toBeInTheDocument()
    expect(baseUrlInput).toHaveValue('http://localhost:11434')
  })

  it('renders model input', () => {
    renderWithProviders(<LlmSettingsForm {...defaultProps} />)

    // Model field should be present (either Select or TextInput)
    expect(screen.getByLabelText(/model/i)).toBeInTheDocument()
  })

  it('calls onProviderChange when provider is changed', async () => {
    const { user } = renderWithProviders(<LlmSettingsForm {...defaultProps} />)

    // Open the provider dropdown
    const providerInput = screen.getByRole('textbox', { name: /provider/i })
    await user.click(providerInput)

    // Wait for dropdown options to appear
    await waitFor(() => {
      expect(screen.getByText('OpenAI')).toBeInTheDocument()
    })

    // Select OpenAI
    await user.click(screen.getByText('OpenAI'))

    expect(defaultProps.onProviderChange).toHaveBeenCalledWith('openai')
  })

  it('calls onBaseUrlChange with default URL when switching to ollama', async () => {
    const props = {
      ...defaultProps,
      provider: 'openai',
      baseUrl: '',
    }
    const { user } = renderWithProviders(<LlmSettingsForm {...props} />)

    // Open the provider dropdown
    const providerInput = screen.getByRole('textbox', { name: /provider/i })
    await user.click(providerInput)

    // Wait for dropdown options to appear
    await waitFor(() => {
      expect(screen.getByText('Ollama')).toBeInTheDocument()
    })

    // Select Ollama
    await user.click(screen.getByText('Ollama'))

    expect(props.onProviderChange).toHaveBeenCalledWith('ollama')
    expect(props.onBaseUrlChange).toHaveBeenCalledWith('http://localhost:11434')
  })

  it('calls onBaseUrlChange with empty string when switching to openai', async () => {
    const { user } = renderWithProviders(<LlmSettingsForm {...defaultProps} />)

    // Open the provider dropdown
    const providerInput = screen.getByRole('textbox', { name: /provider/i })
    await user.click(providerInput)

    // Wait for dropdown options to appear
    await waitFor(() => {
      expect(screen.getByText('OpenAI')).toBeInTheDocument()
    })

    // Select OpenAI
    await user.click(screen.getByText('OpenAI'))

    expect(defaultProps.onProviderChange).toHaveBeenCalledWith('openai')
    expect(defaultProps.onBaseUrlChange).toHaveBeenCalledWith('')
  })

  it('calls onModelChange when model is changed', async () => {
    const { user } = renderWithProviders(<LlmSettingsForm {...defaultProps} />)

    // Wait for models to load (debounce 500ms + query time)
    await waitFor(
      () => {
        const modelInput = screen.getByRole('textbox', { name: /model/i })
        expect(modelInput).toBeInTheDocument()
      },
      { timeout: 2000 }
    )

    // Open the model dropdown
    const modelInput = screen.getByRole('textbox', { name: /model/i })
    await user.click(modelInput)

    // Wait for options to appear
    await waitFor(() => {
      expect(screen.getByText('llama2')).toBeInTheDocument()
    })

    // Select llama2
    await user.click(screen.getByText('llama2'))

    expect(defaultProps.onModelChange).toHaveBeenCalledWith('llama2')
  })

  it('calls onBaseUrlChange when base URL is edited', async () => {
    const { user } = renderWithProviders(<LlmSettingsForm {...defaultProps} />)

    const baseUrlInput = screen.getByLabelText(/base url/i)
    await user.clear(baseUrlInput)
    await user.type(baseUrlInput, 'http://custom:11434')

    expect(defaultProps.onBaseUrlChange).toHaveBeenCalled()
  })

  it('displays alert when Ollama connection fails', async () => {
    // Set up error response
    server.use(
      http.get(`${BASE_URL}/api/ollama/models`, () => {
        return HttpResponse.json({ detail: 'Connection refused' }, { status: 500 })
      })
    )

    renderWithProviders(<LlmSettingsForm {...defaultProps} />)

    // Wait for error alert to appear
    await waitFor(() => {
      expect(screen.getByText(/ollamaサーバーに接続できません/i)).toBeInTheDocument()
    })
  })

  it('displays TextInput for model when Ollama connection fails', async () => {
    // Set up error response
    server.use(
      http.get(`${BASE_URL}/api/ollama/models`, () => {
        return HttpResponse.json({ detail: 'Connection refused' }, { status: 500 })
      })
    )

    const onModelChange = vi.fn()
    const props = { ...defaultProps, onModelChange }

    const { user } = renderWithProviders(<LlmSettingsForm {...props} />)

    // Wait for error state (debounce 500ms + query time)
    await waitFor(
      () => {
        expect(screen.getByText(/ollamaサーバーに接続できません/i)).toBeInTheDocument()
      },
      { timeout: 2000 }
    )

    // Model should be a TextInput (can type in it)
    const modelInput = screen.getByLabelText(/model/i)
    await user.clear(modelInput)
    await user.type(modelInput, 'x')

    expect(onModelChange).toHaveBeenCalled()
  })

  it('displays Select for model when Ollama connection succeeds', async () => {
    renderWithProviders(<LlmSettingsForm {...defaultProps} />)

    // Wait for models to load
    await waitFor(() => {
      // The Select component should be rendered with searchable option
      const modelInput = screen.getByRole('textbox', { name: /model/i })
      expect(modelInput).toBeInTheDocument()
    })

    // No error alert should be displayed
    expect(screen.queryByText(/ollamaサーバーに接続できません/i)).not.toBeInTheDocument()
  })

  it('uses custom modelLabel when provided', () => {
    renderWithProviders(
      <LlmSettingsForm {...defaultProps} modelLabel="LLM Model" />
    )

    expect(screen.getByLabelText(/llm model/i)).toBeInTheDocument()
  })

  it('displays TextInput for model when provider is openai', () => {
    const props = {
      ...defaultProps,
      provider: 'openai',
      model: 'gpt-4',
      baseUrl: 'https://api.openai.com/v1',
    }
    renderWithProviders(<LlmSettingsForm {...props} />)

    // For OpenAI, model should be a TextInput with placeholder
    const modelInput = screen.getByLabelText(/model/i)
    expect(modelInput).toBeInTheDocument()
    expect(modelInput).toHaveAttribute('placeholder', 'e.g., gpt-4')
  })

  it('shows correct placeholder for Ollama TextInput', async () => {
    // Set up error response to force TextInput
    server.use(
      http.get(`${BASE_URL}/api/ollama/models`, () => {
        return HttpResponse.json({ detail: 'Connection refused' }, { status: 500 })
      })
    )

    renderWithProviders(<LlmSettingsForm {...defaultProps} />)

    // Wait for error state (debounce 500ms + query time)
    await waitFor(
      () => {
        expect(screen.getByText(/ollamaサーバーに接続できません/i)).toBeInTheDocument()
      },
      { timeout: 2000 }
    )

    const modelInput = screen.getByLabelText(/model/i)
    expect(modelInput).toHaveAttribute('placeholder', 'e.g., llama3.2')
  })

  it('shows correct description for base URL based on provider', () => {
    // Ollama provider
    const { rerender } = renderWithProviders(<LlmSettingsForm {...defaultProps} />)
    expect(screen.getByText(/ollama server url/i)).toBeInTheDocument()

    // OpenAI provider
    rerender(
      <QueryClientProvider
        client={
          new QueryClient({
            defaultOptions: { queries: { retry: false } },
          })
        }
      >
        <MantineProvider>
          <LlmSettingsForm
            {...defaultProps}
            provider="openai"
            baseUrl="https://api.openai.com/v1"
          />
        </MantineProvider>
      </QueryClientProvider>
    )
    expect(
      screen.getByText(/custom api endpoint for openai-compatible providers/i)
    ).toBeInTheDocument()
  })
})
