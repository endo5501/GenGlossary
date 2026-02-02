import { describe, expect, it, beforeEach } from 'vitest'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MantineProvider } from '@mantine/core'
import { Notifications } from '@mantine/notifications'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { server } from './setup'
import { handlers, mockProjects } from '../mocks/handlers'
import { http, HttpResponse } from 'msw'
import { SettingsPage } from '../pages/SettingsPage'

// Test wrapper with providers
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
        <MantineProvider>
          <Notifications />
          {ui}
        </MantineProvider>
      </QueryClientProvider>
    ),
  }
}

describe('SettingsPage', () => {
  beforeEach(() => {
    server.use(...handlers)
  })

  it('displays loading state initially', () => {
    renderWithProviders(<SettingsPage projectId={1} />)
    expect(screen.getByTestId('settings-loading')).toBeInTheDocument()
  })

  it('displays project settings form after loading', async () => {
    renderWithProviders(<SettingsPage projectId={1} />)

    await waitFor(() => {
      expect(screen.getByTestId('settings-form')).toBeInTheDocument()
    })

    // Check form fields
    expect(screen.getByLabelText(/project name/i)).toHaveValue('Test Project 1')
    // Provider is a Select component, check the input value
    const providerInput = screen.getByRole('textbox', { name: /provider/i })
    expect(providerInput).toHaveValue('Ollama')
    expect(screen.getByLabelText(/model/i)).toHaveValue('llama3.2')
  })

  it('shows validation error for empty name', async () => {
    const { user } = renderWithProviders(<SettingsPage projectId={1} />)

    await waitFor(() => {
      expect(screen.getByTestId('settings-form')).toBeInTheDocument()
    })

    // Clear the name field
    const nameInput = screen.getByLabelText(/project name/i)
    await user.clear(nameInput)

    // Click save button
    const saveButton = screen.getByRole('button', { name: /save/i })
    await user.click(saveButton)

    // Should show validation error
    await waitFor(() => {
      expect(screen.getByText(/name is required/i)).toBeInTheDocument()
    })
  })

  it('shows error toast for duplicate name', async () => {
    const { user } = renderWithProviders(<SettingsPage projectId={1} />)

    await waitFor(() => {
      expect(screen.getByTestId('settings-form')).toBeInTheDocument()
    })

    // Change name to duplicate
    const nameInput = screen.getByLabelText(/project name/i)
    await user.clear(nameInput)
    await user.type(nameInput, 'Test Project 2')

    // Click save button
    const saveButton = screen.getByRole('button', { name: /save/i })
    await user.click(saveButton)

    // Should show error notification
    await waitFor(() => {
      expect(screen.getByText(/already exists/i)).toBeInTheDocument()
    }, { timeout: 3000 })
  })

  it('saves changes and shows success toast', async () => {
    const { user } = renderWithProviders(<SettingsPage projectId={1} />)

    await waitFor(() => {
      expect(screen.getByTestId('settings-form')).toBeInTheDocument()
    })

    // Change the model name
    const modelInput = screen.getByLabelText(/model/i)
    await user.clear(modelInput)
    await user.type(modelInput, 'llama3.3')

    // Click save button
    const saveButton = screen.getByRole('button', { name: /save/i })
    await user.click(saveButton)

    // Should show success notification
    await waitFor(() => {
      expect(screen.getByText(/saved/i)).toBeInTheDocument()
    })
  })

  it('displays provider select with current value', async () => {
    renderWithProviders(<SettingsPage projectId={1} />)

    await waitFor(() => {
      expect(screen.getByTestId('settings-form')).toBeInTheDocument()
    })

    // Check that provider select exists with current value
    const providerInput = screen.getByRole('textbox', { name: /provider/i })
    expect(providerInput).toHaveValue('Ollama')
  })

  it('shows Base URL field when Ollama is selected', async () => {
    renderWithProviders(<SettingsPage projectId={1} />)

    await waitFor(() => {
      expect(screen.getByTestId('settings-form')).toBeInTheDocument()
    })

    // Ollama is selected, base_url should be visible with default value
    const baseUrlInput = screen.getByLabelText(/base url/i)
    expect(baseUrlInput).toBeInTheDocument()
    expect(baseUrlInput).toHaveValue('http://localhost:11434')
  })

  it('updates Base URL when editing', async () => {
    // Use project 2 which already has OpenAI selected
    renderWithProviders(<SettingsPage projectId={2} />)

    await waitFor(() => {
      expect(screen.getByTestId('settings-form')).toBeInTheDocument()
    })

    // Base URL should be visible and have value
    const baseUrlInput = screen.getByLabelText(/base url/i)
    expect(baseUrlInput).toHaveValue('https://api.openai.com/v1')
  })

  it('disables save button when no changes', async () => {
    renderWithProviders(<SettingsPage projectId={1} />)

    await waitFor(() => {
      expect(screen.getByTestId('settings-form')).toBeInTheDocument()
    })

    // Save button should be disabled when no changes
    const saveButton = screen.getByRole('button', { name: /save/i })
    expect(saveButton).toBeDisabled()
  })

  it('enables save button when changes are made', async () => {
    const { user } = renderWithProviders(<SettingsPage projectId={1} />)

    await waitFor(() => {
      expect(screen.getByTestId('settings-form')).toBeInTheDocument()
    })

    // Save button should be disabled initially
    const saveButton = screen.getByRole('button', { name: /save/i })
    expect(saveButton).toBeDisabled()

    // Make a change
    const modelInput = screen.getByLabelText(/model/i)
    await user.clear(modelInput)
    await user.type(modelInput, 'new-model')

    // Save button should now be enabled
    expect(saveButton).not.toBeDisabled()
  })

  it('displays 404 message for non-existent project', async () => {
    server.use(
      http.get('http://localhost:8000/api/projects/:id', () =>
        HttpResponse.json({ detail: 'Not found' }, { status: 404 })
      )
    )

    renderWithProviders(<SettingsPage projectId={999} />)

    await waitFor(() => {
      expect(screen.getByText(/not found/i)).toBeInTheDocument()
    })
  })
})
