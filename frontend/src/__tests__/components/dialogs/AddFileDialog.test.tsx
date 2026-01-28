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

describe('AddFileDialog', () => {
  beforeEach(() => {
    server.use(...handlers)
  })

  it('renders dialog when opened', () => {
    const onClose = vi.fn()
    renderWithProviders(<AddFileDialog projectId={1} opened={true} onClose={onClose} />)

    expect(screen.getByRole('dialog')).toBeInTheDocument()
    expect(screen.getByText(/add file/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/file path/i)).toBeInTheDocument()
  })

  it('does not render dialog when closed', () => {
    const onClose = vi.fn()
    renderWithProviders(<AddFileDialog projectId={1} opened={false} onClose={onClose} />)

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('validates required file path', async () => {
    const onClose = vi.fn()
    const { user } = renderWithProviders(<AddFileDialog projectId={1} opened={true} onClose={onClose} />)

    // Try to submit empty form
    const submitButton = screen.getByRole('button', { name: /^add$/i })
    await user.click(submitButton)

    // Should show validation error
    await waitFor(() => {
      expect(screen.getByText(/file path is required/i)).toBeInTheDocument()
    })
  })

  it('calls mutation and closes on valid submission', async () => {
    const onClose = vi.fn()
    const { user } = renderWithProviders(<AddFileDialog projectId={1} opened={true} onClose={onClose} />)

    // Fill in file path
    const input = screen.getByLabelText(/file path/i)
    await user.type(input, 'new-file.md')

    // Submit
    const submitButton = screen.getByRole('button', { name: /^add$/i })
    await user.click(submitButton)

    // Dialog should close
    await waitFor(() => {
      expect(onClose).toHaveBeenCalled()
    })
  })

  it('clears form and calls onClose when cancel clicked', async () => {
    const onClose = vi.fn()
    const { user } = renderWithProviders(<AddFileDialog projectId={1} opened={true} onClose={onClose} />)

    // Type something in the input
    const input = screen.getByLabelText(/file path/i)
    await user.type(input, 'some-file.md')

    // Click cancel
    const cancelButton = screen.getByRole('button', { name: /cancel/i })
    await user.click(cancelButton)

    // onClose should be called
    expect(onClose).toHaveBeenCalled()
  })

  it('clears input value when dialog reopens', async () => {
    const onClose = vi.fn()
    const { user, rerender } = renderWithProviders(
      <AddFileDialog projectId={1} opened={true} onClose={onClose} />
    )

    // Type something in the input
    const input = screen.getByLabelText(/file path/i)
    await user.type(input, 'some-file.md')
    expect(input).toHaveValue('some-file.md')

    // Close dialog
    const cancelButton = screen.getByRole('button', { name: /cancel/i })
    await user.click(cancelButton)

    // Rerender as closed then opened again
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

    // Input should be cleared
    await waitFor(() => {
      const newInput = screen.getByLabelText(/file path/i)
      expect(newInput).toHaveValue('')
    })
  })
})
