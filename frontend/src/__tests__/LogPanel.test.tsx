import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MantineProvider } from '@mantine/core'
import { LogPanel } from '../components/layout/LogPanel'
import { useLogStore } from '../store/logStore'
import type { LogMessage } from '../api/types'

function renderWithMantine(ui: React.ReactElement) {
  return render(<MantineProvider>{ui}</MantineProvider>)
}

describe('LogPanel Progress Display', () => {
  beforeEach(() => {
    // Reset store before each test
    useLogStore.getState().clearLogs()
    useLogStore.getState().setCurrentRunId(null)
  })

  it('displays progress bar when progress data exists', () => {
    // Add a log with progress data
    const logWithProgress: LogMessage = {
      run_id: 1,
      level: 'info',
      message: 'term1: 50%',
      timestamp: '2025-01-01T00:00:00Z',
      step: 'provisional',
      progress_current: 5,
      progress_total: 10,
      current_term: 'term1',
    }

    useLogStore.getState().setCurrentRunId(1)
    useLogStore.getState().addLog(logWithProgress)

    renderWithMantine(<LogPanel projectId={1} runId={1} />)

    // Should show progress bar
    expect(screen.getByTestId('progress-bar')).toBeInTheDocument()
  })

  it('displays current step name', () => {
    const logWithProgress: LogMessage = {
      run_id: 1,
      level: 'info',
      message: 'term1: 50%',
      timestamp: '2025-01-01T00:00:00Z',
      step: 'provisional',
      progress_current: 5,
      progress_total: 10,
      current_term: 'term1',
    }

    useLogStore.getState().setCurrentRunId(1)
    useLogStore.getState().addLog(logWithProgress)

    renderWithMantine(<LogPanel projectId={1} runId={1} />)

    // Should show step name
    expect(screen.getByText(/provisional/i)).toBeInTheDocument()
  })

  it('displays current term being processed', () => {
    const logWithProgress: LogMessage = {
      run_id: 1,
      level: 'info',
      message: 'quantum computer: 50%',
      timestamp: '2025-01-01T00:00:00Z',
      step: 'provisional',
      progress_current: 5,
      progress_total: 10,
      current_term: 'quantum computer',
    }

    useLogStore.getState().setCurrentRunId(1)
    useLogStore.getState().addLog(logWithProgress)

    renderWithMantine(<LogPanel projectId={1} runId={1} />)

    // Should show current term (in progress display, not just in log message)
    // The progress display shows "step: term" format
    expect(screen.getByText(/provisional: quantum computer/)).toBeInTheDocument()
  })

  it('displays progress count (current/total)', () => {
    const logWithProgress: LogMessage = {
      run_id: 1,
      level: 'info',
      message: 'term1: 50%',
      timestamp: '2025-01-01T00:00:00Z',
      step: 'provisional',
      progress_current: 5,
      progress_total: 10,
      current_term: 'term1',
    }

    useLogStore.getState().setCurrentRunId(1)
    useLogStore.getState().addLog(logWithProgress)

    renderWithMantine(<LogPanel projectId={1} runId={1} />)

    // Should show 5/10 or similar format
    expect(screen.getByText(/5.*\/.*10/)).toBeInTheDocument()
  })

  it('does not display progress bar when no progress data', () => {
    const logWithoutProgress: LogMessage = {
      run_id: 1,
      level: 'info',
      message: 'Starting pipeline...',
      timestamp: '2025-01-01T00:00:00Z',
    }

    useLogStore.getState().setCurrentRunId(1)
    useLogStore.getState().addLog(logWithoutProgress)

    renderWithMantine(<LogPanel projectId={1} runId={1} />)

    // Should not show progress bar
    expect(screen.queryByTestId('progress-bar')).not.toBeInTheDocument()
  })
})
