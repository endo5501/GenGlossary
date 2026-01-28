import { describe, expect, it, beforeEach } from 'vitest'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MantineProvider } from '@mantine/core'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { server } from './setup'
import { handlers, mockProjects, mockFiles } from '../mocks/handlers'
import { http, HttpResponse } from 'msw'
import { HomePage } from '../pages/HomePage'
import { FilesPage } from '../pages/FilesPage'

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
        <MantineProvider>{ui}</MantineProvider>
      </QueryClientProvider>
    ),
  }
}

describe('HomePage (Projects)', () => {
  beforeEach(() => {
    server.use(...handlers)
  })

  it('displays loading state initially', () => {
    renderWithProviders(<HomePage />)
    expect(screen.getByTestId('projects-loading')).toBeInTheDocument()
  })

  it('displays empty state when no projects exist', async () => {
    server.use(http.get('http://localhost:8000/api/projects', () => HttpResponse.json([])))

    renderWithProviders(<HomePage />)

    await waitFor(() => {
      expect(screen.getByTestId('projects-empty')).toBeInTheDocument()
    })
    expect(screen.getByText(/no projects/i)).toBeInTheDocument()
  })

  it('displays project list with statistics columns', async () => {
    renderWithProviders(<HomePage />)

    await waitFor(() => {
      expect(screen.getByText('Test Project 1')).toBeInTheDocument()
    })
    expect(screen.getByText('Test Project 2')).toBeInTheDocument()

    // Check table headers for statistics columns
    expect(screen.getByText('Doc')).toBeInTheDocument()
    expect(screen.getByText('用語')).toBeInTheDocument()
    expect(screen.getByText('issues')).toBeInTheDocument()
  })

  it('selects project on click and shows summary card', async () => {
    const { user } = renderWithProviders(<HomePage />)

    await waitFor(() => {
      expect(screen.getByText('Test Project 1')).toBeInTheDocument()
    })

    // Click on first project
    await user.click(screen.getByText('Test Project 1'))

    // Summary card should appear
    await waitFor(() => {
      expect(screen.getByTestId('project-summary-card')).toBeInTheDocument()
    })

    const summaryCard = screen.getByTestId('project-summary-card')
    expect(within(summaryCard).getByText('Test Project 1')).toBeInTheDocument()
    expect(within(summaryCard).getByText(/ollama/i)).toBeInTheDocument()
    expect(within(summaryCard).getByText(/llama3.2/i)).toBeInTheDocument()
  })

  it('opens create project dialog when clicking create button', async () => {
    const { user } = renderWithProviders(<HomePage />)

    await waitFor(() => {
      expect(screen.getByText('Test Project 1')).toBeInTheDocument()
    })

    // Click create button (now in Japanese and at bottom of list)
    const createButton = screen.getByRole('button', { name: /新規作成/i })
    await user.click(createButton)

    // Dialog should open
    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument()
    })
    expect(screen.getByLabelText(/project name/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/document root/i)).toBeInTheDocument()
  })
})

describe('Create Project Dialog', () => {
  beforeEach(() => {
    server.use(...handlers)
  })

  it('validates required fields', async () => {
    const { user } = renderWithProviders(<HomePage />)

    await waitFor(() => {
      expect(screen.getByText('Test Project 1')).toBeInTheDocument()
    })

    // Open dialog - click 新規作成 button (at bottom of list)
    const createButton = screen.getByRole('button', { name: /新規作成/i })
    await user.click(createButton)

    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument()
    })

    // Try to submit empty form - get button within dialog
    const dialog = screen.getByRole('dialog')
    const submitButton = within(dialog).getByRole('button', { name: /^create$/i })
    await user.click(submitButton)

    // Should show validation errors
    await waitFor(() => {
      expect(screen.getByText(/name is required/i)).toBeInTheDocument()
    })
  })

  it('creates project on valid submission', async () => {
    const { user } = renderWithProviders(<HomePage />)

    await waitFor(() => {
      expect(screen.getByText('Test Project 1')).toBeInTheDocument()
    })

    // Open dialog - click 新規作成 button (at bottom of list)
    const createButton = screen.getByRole('button', { name: /新規作成/i })
    await user.click(createButton)

    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument()
    })

    // Fill form
    await user.type(screen.getByLabelText(/project name/i), 'New Test Project')
    await user.type(screen.getByLabelText(/document root/i), '/path/to/new/docs')

    // Submit - get button within dialog
    const dialog = screen.getByRole('dialog')
    const submitButton = within(dialog).getByRole('button', { name: /^create$/i })
    await user.click(submitButton)

    // Dialog should close
    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    })
  })

  it('has LLM Provider as dropdown with ollama and openai options', async () => {
    const { user } = renderWithProviders(<HomePage />)

    await waitFor(() => {
      expect(screen.getByText('Test Project 1')).toBeInTheDocument()
    })

    // Open dialog
    const createButton = screen.getByRole('button', { name: /新規作成/i })
    await user.click(createButton)

    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument()
    })

    // LLM Provider should be a combobox (Select component)
    const providerSelect = screen.getByRole('textbox', { name: /llm provider/i })
    expect(providerSelect).toBeInTheDocument()

    // Click to open dropdown
    await user.click(providerSelect)

    // Should show ollama and openai options
    await waitFor(() => {
      expect(screen.getByRole('option', { name: /ollama/i })).toBeInTheDocument()
    })
    expect(screen.getByRole('option', { name: /openai/i })).toBeInTheDocument()
  })
})

describe('Delete Project Dialog', () => {
  beforeEach(() => {
    server.use(...handlers)
  })

  it('shows confirmation before deleting', async () => {
    const { user } = renderWithProviders(<HomePage />)

    await waitFor(() => {
      expect(screen.getByText('Test Project 1')).toBeInTheDocument()
    })

    // Select a project first
    await user.click(screen.getByText('Test Project 1'))

    await waitFor(() => {
      expect(screen.getByTestId('project-summary-card')).toBeInTheDocument()
    })

    // Click delete button in summary card
    const deleteButton = screen.getByRole('button', { name: /delete/i })
    await user.click(deleteButton)

    // Confirmation dialog should appear
    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument()
    })
    expect(screen.getByText(/are you sure/i)).toBeInTheDocument()
  })
})

describe('FilesPage', () => {
  beforeEach(() => {
    server.use(...handlers)
  })

  it('displays file list for project', async () => {
    renderWithProviders(<FilesPage projectId={1} />)

    await waitFor(() => {
      expect(screen.getByText('doc1.md')).toBeInTheDocument()
    })
    expect(screen.getByText('doc2.txt')).toBeInTheDocument()
    expect(screen.getByText('subdir/doc3.md')).toBeInTheDocument()
  })

  it('displays empty state when no files', async () => {
    server.use(
      http.get('http://localhost:8000/api/projects/:projectId/files', () =>
        HttpResponse.json([])
      )
    )

    renderWithProviders(<FilesPage projectId={1} />)

    await waitFor(() => {
      expect(screen.getByTestId('files-empty')).toBeInTheDocument()
    })
  })

  it('runs diff-scan when clicking scan button', async () => {
    const { user } = renderWithProviders(<FilesPage projectId={1} />)

    await waitFor(() => {
      expect(screen.getByText('doc1.md')).toBeInTheDocument()
    })

    // Click scan button
    const scanButton = screen.getByRole('button', { name: /scan/i })
    await user.click(scanButton)

    // Should show scan results
    await waitFor(() => {
      expect(screen.getByTestId('diff-scan-results')).toBeInTheDocument()
    })
    expect(screen.getByText(/new_file.md/)).toBeInTheDocument()
  })
})
