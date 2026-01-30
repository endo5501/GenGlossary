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
      // Set currentRunId to match log run_id
      useLogStore.getState().setCurrentRunId(1)

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
      // Set currentRunId to match log run_id
      useLogStore.getState().setCurrentRunId(1)

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
      // Set currentRunId to match log run_id
      useLogStore.getState().setCurrentRunId(1)

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
      // Set initial run ID
      useLogStore.getState().setCurrentRunId(1)

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

  describe('setCurrentContext', () => {
    beforeEach(() => {
      // Reset store before each test
      useLogStore.getState().clearLogs()
      useLogStore.getState().setCurrentContext(null, null)
    })

    it('sets both project ID and run ID', () => {
      useLogStore.getState().setCurrentContext(1, 42)

      expect(useLogStore.getState().currentProjectId).toBe(1)
      expect(useLogStore.getState().currentRunId).toBe(42)
    })

    it('clears logs when project ID changes', () => {
      useLogStore.getState().setCurrentContext(1, 1)

      const log: LogMessage = {
        run_id: 1,
        level: 'info',
        message: 'Test message',
        timestamp: '2025-01-01T00:00:00Z',
      }

      useLogStore.getState().addLog(log)
      expect(useLogStore.getState().logs).toHaveLength(1)

      // Change project ID only
      useLogStore.getState().setCurrentContext(2, 1)

      expect(useLogStore.getState().logs).toHaveLength(0)
      expect(useLogStore.getState().currentProjectId).toBe(2)
    })

    it('clears logs when run ID changes within same project', () => {
      useLogStore.getState().setCurrentContext(1, 1)

      const log: LogMessage = {
        run_id: 1,
        level: 'info',
        message: 'Test message',
        timestamp: '2025-01-01T00:00:00Z',
      }

      useLogStore.getState().addLog(log)
      expect(useLogStore.getState().logs).toHaveLength(1)

      // Change run ID only
      useLogStore.getState().setCurrentContext(1, 2)

      expect(useLogStore.getState().logs).toHaveLength(0)
      expect(useLogStore.getState().currentRunId).toBe(2)
    })

    it('does not clear logs when both project ID and run ID are the same', () => {
      useLogStore.getState().setCurrentContext(1, 1)

      const log: LogMessage = {
        run_id: 1,
        level: 'info',
        message: 'Test message',
        timestamp: '2025-01-01T00:00:00Z',
      }

      useLogStore.getState().addLog(log)
      expect(useLogStore.getState().logs).toHaveLength(1)

      // Set same context again
      useLogStore.getState().setCurrentContext(1, 1)

      expect(useLogStore.getState().logs).toHaveLength(1)
    })

    it('prevents log collision between different projects with same run ID', () => {
      // Project 1, Run 1 - add log
      useLogStore.getState().setCurrentContext(1, 1)
      const log1: LogMessage = {
        run_id: 1,
        level: 'info',
        message: 'Project 1 log',
        timestamp: '2025-01-01T00:00:00Z',
      }
      useLogStore.getState().addLog(log1)
      expect(useLogStore.getState().logs).toHaveLength(1)
      expect(useLogStore.getState().logs[0].message).toBe('Project 1 log')

      // Switch to Project 2, Run 1 (same run ID, different project)
      useLogStore.getState().setCurrentContext(2, 1)

      // Logs should be cleared to prevent collision
      expect(useLogStore.getState().logs).toHaveLength(0)

      // Add new log for Project 2
      const log2: LogMessage = {
        run_id: 1,
        level: 'info',
        message: 'Project 2 log',
        timestamp: '2025-01-01T00:00:01Z',
      }
      useLogStore.getState().addLog(log2)
      expect(useLogStore.getState().logs).toHaveLength(1)
      expect(useLogStore.getState().logs[0].message).toBe('Project 2 log')
    })
  })

  describe('addLog context validation', () => {
    beforeEach(() => {
      useLogStore.getState().clearLogs()
      useLogStore.getState().setCurrentContext(null, null)
    })

    it('ignores logs when currentRunId is null', () => {
      // currentRunId is null (not set)
      const log: LogMessage = {
        run_id: 1,
        level: 'info',
        message: 'Test message',
        timestamp: '2025-01-01T00:00:00Z',
      }

      useLogStore.getState().addLog(log)

      // Log should be ignored because currentRunId is null
      expect(useLogStore.getState().logs).toHaveLength(0)
    })

    it('adds logs when run_id matches currentRunId', () => {
      useLogStore.getState().setCurrentContext(1, 42)

      const log: LogMessage = {
        run_id: 42,
        level: 'info',
        message: 'Test message',
        timestamp: '2025-01-01T00:00:00Z',
      }

      useLogStore.getState().addLog(log)

      expect(useLogStore.getState().logs).toHaveLength(1)
      expect(useLogStore.getState().logs[0]).toEqual(log)
    })

    it('ignores logs when run_id does not match currentRunId', () => {
      useLogStore.getState().setCurrentContext(1, 42)

      const staleLog: LogMessage = {
        run_id: 41, // Different run_id (stale SSE message)
        level: 'info',
        message: 'Stale message from old run',
        timestamp: '2025-01-01T00:00:00Z',
      }

      useLogStore.getState().addLog(staleLog)

      // Stale log should be ignored
      expect(useLogStore.getState().logs).toHaveLength(0)
    })

    it('does not update latestProgress when log run_id does not match', () => {
      useLogStore.getState().setCurrentContext(1, 42)

      const staleProgressLog: LogMessage = {
        run_id: 41, // Different run_id
        level: 'info',
        message: 'Stale progress',
        timestamp: '2025-01-01T00:00:00Z',
        step: 'provisional',
        progress_current: 5,
        progress_total: 20,
        current_term: 'term1',
      }

      useLogStore.getState().addLog(staleProgressLog)

      // latestProgress should not be updated
      expect(useLogStore.getState().latestProgress).toBeNull()
    })

    it('handles context switch with stale messages correctly', () => {
      // Start with run 1
      useLogStore.getState().setCurrentContext(1, 1)

      const log1: LogMessage = {
        run_id: 1,
        level: 'info',
        message: 'Run 1 message',
        timestamp: '2025-01-01T00:00:00Z',
      }

      useLogStore.getState().addLog(log1)
      expect(useLogStore.getState().logs).toHaveLength(1)

      // Switch to run 2 (this clears logs)
      useLogStore.getState().setCurrentContext(1, 2)
      expect(useLogStore.getState().logs).toHaveLength(0)

      // Stale message from run 1 arrives (simulating slow SSE)
      const staleLog: LogMessage = {
        run_id: 1,
        level: 'info',
        message: 'Stale message from run 1',
        timestamp: '2025-01-01T00:00:01Z',
      }

      useLogStore.getState().addLog(staleLog)

      // Stale log should be ignored
      expect(useLogStore.getState().logs).toHaveLength(0)

      // New message from run 2 should be added
      const newLog: LogMessage = {
        run_id: 2,
        level: 'info',
        message: 'Run 2 message',
        timestamp: '2025-01-01T00:00:02Z',
      }

      useLogStore.getState().addLog(newLog)
      expect(useLogStore.getState().logs).toHaveLength(1)
      expect(useLogStore.getState().logs[0].message).toBe('Run 2 message')
    })
  })

  describe('latestProgress', () => {
    it('returns null when no progress logs exist', () => {
      expect(useLogStore.getState().latestProgress).toBeNull()
    })

    it('updates latestProgress when log with progress data is added', () => {
      // Set currentRunId to match log run_id
      useLogStore.getState().setCurrentRunId(1)

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

      const progress = useLogStore.getState().latestProgress

      expect(progress).toEqual({
        step: 'provisional',
        current: 10,
        total: 20,
        currentTerm: 'term2',
      })
    })

    it('preserves latestProgress when non-progress log is added', () => {
      // Set currentRunId to match log run_id
      useLogStore.getState().setCurrentRunId(1)

      const progressLog: LogMessage = {
        run_id: 1,
        level: 'info',
        message: 'term1: 50%',
        timestamp: '2025-01-01T00:00:00Z',
        step: 'provisional',
        progress_current: 5,
        progress_total: 10,
        current_term: 'term1',
      }

      const regularLog: LogMessage = {
        run_id: 1,
        level: 'info',
        message: 'Some other message',
        timestamp: '2025-01-01T00:00:01Z',
      }

      useLogStore.getState().addLog(progressLog)
      useLogStore.getState().addLog(regularLog)

      const progress = useLogStore.getState().latestProgress

      expect(progress).toEqual({
        step: 'provisional',
        current: 5,
        total: 10,
        currentTerm: 'term1',
      })
    })

    it('clears latestProgress when logs are cleared', () => {
      // Set currentRunId to match log run_id
      useLogStore.getState().setCurrentRunId(1)

      const progressLog: LogMessage = {
        run_id: 1,
        level: 'info',
        message: 'term1: 50%',
        timestamp: '2025-01-01T00:00:00Z',
        step: 'provisional',
        progress_current: 5,
        progress_total: 10,
        current_term: 'term1',
      }

      useLogStore.getState().addLog(progressLog)
      expect(useLogStore.getState().latestProgress).not.toBeNull()

      useLogStore.getState().clearLogs()
      expect(useLogStore.getState().latestProgress).toBeNull()
    })
  })
})
