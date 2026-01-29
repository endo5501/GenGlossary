import { describe, it, expect, beforeEach } from 'vitest'
import { useLogStore } from '../store/logStore'
import type { LogMessage } from '../api/types'

describe('logStore', () => {
  beforeEach(() => {
    // Reset store before each test
    useLogStore.getState().clearLogs()
    useLogStore.getState().setCurrentRunId(null)
  })

  describe('addLog', () => {
    it('adds a log message to the store', () => {
      const log: LogMessage = {
        run_id: 1,
        level: 'info',
        message: 'Test message',
        timestamp: '2025-01-01T00:00:00Z',
      }

      useLogStore.getState().addLog(log)

      expect(useLogStore.getState().logs).toHaveLength(1)
      expect(useLogStore.getState().logs[0]).toEqual(log)
    })

    it('limits logs to 1000 entries', () => {
      const logs: LogMessage[] = Array.from({ length: 1100 }, (_, i) => ({
        run_id: 1,
        level: 'info' as const,
        message: `Message ${i}`,
        timestamp: '2025-01-01T00:00:00Z',
      }))

      logs.forEach((log) => useLogStore.getState().addLog(log))

      expect(useLogStore.getState().logs).toHaveLength(1000)
      // Should keep the most recent logs
      expect(useLogStore.getState().logs[0].message).toBe('Message 100')
      expect(useLogStore.getState().logs[999].message).toBe('Message 1099')
    })
  })

  describe('clearLogs', () => {
    it('clears all logs', () => {
      const log: LogMessage = {
        run_id: 1,
        level: 'info',
        message: 'Test message',
        timestamp: '2025-01-01T00:00:00Z',
      }

      useLogStore.getState().addLog(log)
      expect(useLogStore.getState().logs).toHaveLength(1)

      useLogStore.getState().clearLogs()
      expect(useLogStore.getState().logs).toHaveLength(0)
    })
  })

  describe('setCurrentRunId', () => {
    it('sets the current run ID', () => {
      useLogStore.getState().setCurrentRunId(42)

      expect(useLogStore.getState().currentRunId).toBe(42)
    })

    it('clears logs when run ID changes', () => {
      const log: LogMessage = {
        run_id: 1,
        level: 'info',
        message: 'Test message',
        timestamp: '2025-01-01T00:00:00Z',
      }

      useLogStore.getState().addLog(log)
      expect(useLogStore.getState().logs).toHaveLength(1)

      useLogStore.getState().setCurrentRunId(2)

      expect(useLogStore.getState().logs).toHaveLength(0)
      expect(useLogStore.getState().currentRunId).toBe(2)
    })

    it('does not clear logs when setting same run ID', () => {
      useLogStore.getState().setCurrentRunId(1)

      const log: LogMessage = {
        run_id: 1,
        level: 'info',
        message: 'Test message',
        timestamp: '2025-01-01T00:00:00Z',
      }

      useLogStore.getState().addLog(log)
      expect(useLogStore.getState().logs).toHaveLength(1)

      // Set same run ID again
      useLogStore.getState().setCurrentRunId(1)

      expect(useLogStore.getState().logs).toHaveLength(1)
    })
  })

  describe('getLatestProgress', () => {
    it('returns null when no progress logs exist', () => {
      expect(useLogStore.getState().getLatestProgress()).toBeNull()
    })

    it('returns latest progress from logs with progress data', () => {
      const log1: LogMessage = {
        run_id: 1,
        level: 'info',
        message: 'term1: 25%',
        timestamp: '2025-01-01T00:00:00Z',
        step: 'provisional',
        progress_current: 5,
        progress_total: 20,
        current_term: 'term1',
      }

      const log2: LogMessage = {
        run_id: 1,
        level: 'info',
        message: 'term2: 50%',
        timestamp: '2025-01-01T00:00:01Z',
        step: 'provisional',
        progress_current: 10,
        progress_total: 20,
        current_term: 'term2',
      }

      useLogStore.getState().addLog(log1)
      useLogStore.getState().addLog(log2)

      const progress = useLogStore.getState().getLatestProgress()

      expect(progress).toEqual({
        step: 'provisional',
        current: 10,
        total: 20,
        currentTerm: 'term2',
      })
    })
  })
})
