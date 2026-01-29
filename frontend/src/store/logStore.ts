import { create } from 'zustand'
import type { LogMessage } from '../api/types'

export interface LogProgress {
  step: string
  current: number
  total: number
  currentTerm: string
}

interface LogStore {
  logs: LogMessage[]
  currentRunId: number | null
  latestProgress: LogProgress | null
  addLog: (log: LogMessage) => void
  clearLogs: () => void
  setCurrentRunId: (runId: number | null) => void
  getLatestProgress: () => LogProgress | null
}

const MAX_LOGS = 1000

function extractProgress(log: LogMessage): LogProgress | null {
  if (
    log.step !== undefined &&
    log.progress_current !== undefined &&
    log.progress_total !== undefined
  ) {
    return {
      step: log.step,
      current: log.progress_current,
      total: log.progress_total,
      currentTerm: log.current_term ?? '',
    }
  }
  return null
}

export const useLogStore = create<LogStore>((set, get) => ({
  logs: [],
  currentRunId: null,
  latestProgress: null,

  addLog: (log) =>
    set((state) => {
      const newLogs = [...state.logs, log]
      const progress = extractProgress(log)
      return {
        logs: newLogs.length > MAX_LOGS ? newLogs.slice(-MAX_LOGS) : newLogs,
        // Update latestProgress if this log has progress data
        latestProgress: progress ?? state.latestProgress,
      }
    }),

  clearLogs: () => set({ logs: [], latestProgress: null }),

  setCurrentRunId: (runId) =>
    set((state) => {
      if (state.currentRunId !== runId) {
        return { currentRunId: runId, logs: [], latestProgress: null }
      }
      return { currentRunId: runId }
    }),

  // Legacy method for backward compatibility (reads from state directly)
  getLatestProgress: () => get().latestProgress,
}))
