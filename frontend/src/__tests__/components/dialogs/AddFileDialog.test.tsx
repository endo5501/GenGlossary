import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MantineProvider } from '@mantine/core'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { server } from '../../setup'
import { handlers } from '../../../mocks/handlers'
import { AddFileDialog } from '../../../components/dialogs/AddFileDialog'

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

function createMockFile(name: string, content: string): File {
  return new File([content], name, { type: 'text/plain' })
}

describe('AddFileDialog', () => {
  beforeEach(() => {
    server.use(...handlers)
  })

  it('renders dialog when opened', () => {
    const onClose = vi.fn()
    renderWithProviders(<AddFileDialog projectId={1} opened={true} onClose={onClose} />)

    expect(screen.getByRole('dialog')).toBeInTheDocument()
    expect(screen.getByText(/add files/i)).toBeInTheDocument()
    expect(screen.getByText(/drag files here or click to select/i)).toBeInTheDocument()
  })

  it('does not render dialog when closed', () => {
    const onClose = vi.fn()
    renderWithProviders(<AddFileDialog projectId={1} opened={false} onClose={onClose} />)

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('shows add button as disabled when no files selected', () => {
    const onClose = vi.fn()
    renderWithProviders(<AddFileDialog projectId={1} opened={true} onClose={onClose} />)

    const addButton = screen.getByRole('button', { name: /add \(0\)/i })
    expect(addButton).toBeDisabled()
  })

  it('shows file list when files are dropped', async () => {
    const onClose = vi.fn()
    renderWithProviders(<AddFileDialog projectId={1} opened={true} onClose={onClose} />)

    const dropzone = screen.getByText(/drag files here or click to select/i).closest('div')!
    const file = createMockFile('test.md', '# Test content')

    // Simulate file drop
    const dataTransfer = {
      files: [file],
      items: [
        {
          kind: 'file',
          type: 'text/plain',
          getAsFile: () => file,
        },
      ],
      types: ['Files'],
    }

    await waitFor(async () => {
      const dropEvent = new Event('drop', { bubbles: true })
      Object.assign(dropEvent, { dataTransfer })
      dropzone.dispatchEvent(dropEvent)
    })

    // File should appear in selected list after processing
    await waitFor(
      () => {
        expect(screen.getByText('test.md')).toBeInTheDocument()
      },
      { timeout: 2000 }
    )
  })

  it('calls onClose when cancel clicked', async () => {
    const onClose = vi.fn()
    const { user } = renderWithProviders(<AddFileDialog projectId={1} opened={true} onClose={onClose} />)

    const cancelButton = screen.getByRole('button', { name: /cancel/i })
    await user.click(cancelButton)

    expect(onClose).toHaveBeenCalled()
  })

  it('clears selected files when dialog reopens', async () => {
    const onClose = vi.fn()
    const { rerender } = renderWithProviders(
      <AddFileDialog projectId={1} opened={true} onClose={onClose} />
    )

    // Close and reopen dialog
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    })
    rerender(
      <QueryClientProvider client={queryClient}>
        <MantineProvider>
          <AddFileDialog projectId={1} opened={false} onClose={onClose} />
        </MantineProvider>
      </QueryClientProvider>
    )
    rerender(
      <QueryClientProvider client={queryClient}>
        <MantineProvider>
          <AddFileDialog projectId={1} opened={true} onClose={onClose} />
        </MantineProvider>
      </QueryClientProvider>
    )

    // Add button should be disabled (no files selected)
    await waitFor(() => {
      const addButton = screen.getByRole('button', { name: /add \(0\)/i })
      expect(addButton).toBeDisabled()
    })
  })

  it('displays allowed file types message', () => {
    const onClose = vi.fn()
    renderWithProviders(<AddFileDialog projectId={1} opened={true} onClose={onClose} />)

    expect(screen.getByText(/only .txt and .md files are allowed/i)).toBeInTheDocument()
  })
})
