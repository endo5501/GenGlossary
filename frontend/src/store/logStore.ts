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
  currentProjectId: number | null
  currentRunId: number | null
  latestProgress: LogProgress | null
  addLog: (log: LogMessage) => void
  clearLogs: () => void
  setCurrentRunId: (runId: number | null) => void
  setCurrentContext: (projectId: number | null, runId: number | null) => void
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
  currentProjectId: null,
  currentRunId: null,
  latestProgress: null,

  addLog: (log) =>
    set((state) => {
      // Validate context: ignore logs with mismatched run_id
      if (state.currentRunId === null || log.run_id !== state.currentRunId) {
        return state // No state change
      }

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

  setCurrentContext: (projectId, runId) =>
    set((state) => {
      if (state.currentProjectId !== projectId || state.currentRunId !== runId) {
        return {
          currentProjectId: projectId,
          currentRunId: runId,
          logs: [],
          latestProgress: null,
        }
      }
      return { currentProjectId: projectId, currentRunId: runId }
    }),

  // Legacy method for backward compatibility (reads from state directly)
  getLatestProgress: () => get().latestProgress,
}))
