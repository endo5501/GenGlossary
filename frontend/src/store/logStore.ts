import { create } from 'zustand'
import type { LogMessage } from '../api/types'

interface LogProgress {
  step: string
  current: number
  total: number
  currentTerm: string
}

interface LogStore {
  logs: LogMessage[]
  currentRunId: number | null
  addLog: (log: LogMessage) => void
  clearLogs: () => void
  setCurrentRunId: (runId: number | null) => void
  getLatestProgress: () => LogProgress | null
}

const MAX_LOGS = 1000

export const useLogStore = create<LogStore>((set, get) => ({
  logs: [],
  currentRunId: null,

  addLog: (log) =>
    set((state) => {
      const newLogs = [...state.logs, log]
      return {
        logs: newLogs.length > MAX_LOGS ? newLogs.slice(-MAX_LOGS) : newLogs,
      }
    }),

  clearLogs: () => set({ logs: [] }),

  setCurrentRunId: (runId) =>
    set((state) => {
      if (state.currentRunId !== runId) {
        return { currentRunId: runId, logs: [] }
      }
      return { currentRunId: runId }
    }),

  getLatestProgress: () => {
    const { logs } = get()
    // Find the latest log with progress data (iterate from end)
    for (let i = logs.length - 1; i >= 0; i--) {
      const log = logs[i]
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
    }
    return null
  },
}))
