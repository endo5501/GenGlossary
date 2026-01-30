import { useState, useEffect, useCallback } from 'react'
import type { LogMessage } from '../types'
import { getBaseUrl } from '../client'
import { useLogStore } from '../../store/logStore'

interface UseLogStreamOptions {
  onComplete?: () => void
}

interface UseLogStreamResult {
  logs: LogMessage[]
  isConnected: boolean
  error: Error | null
  clearLogs: () => void
}

const parseLogMessage = (event: MessageEvent): LogMessage | null => {
  try {
    return JSON.parse(event.data) as LogMessage
  } catch {
    return null
  }
}

export function useLogStream(
  projectId: number,
  runId: number | undefined,
  options?: UseLogStreamOptions
): UseLogStreamResult {
  // Use Zustand store for logs (persists across page navigations)
  const logs = useLogStore((state) => state.logs)
  const addLog = useLogStore((state) => state.addLog)
  const clearLogs = useLogStore((state) => state.clearLogs)
  const setCurrentContext = useLogStore((state) => state.setCurrentContext)

  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const handleClearLogs = useCallback(() => clearLogs(), [clearLogs])

  // Update context when projectId or runId changes (clears logs when either changes)
  useEffect(() => {
    setCurrentContext(projectId, runId ?? null)
  }, [projectId, runId, setCurrentContext])

  useEffect(() => {
    if (!runId) {
      setIsConnected(false)
      return
    }

    const url = `${getBaseUrl()}/api/projects/${projectId}/runs/${runId}/logs`
    const eventSource = new EventSource(url)

    eventSource.onopen = () => {
      setIsConnected(true)
      setError(null)
    }

    eventSource.onmessage = (event) => {
      const log = parseLogMessage(event)
      if (log) {
        addLog(log)
      }
    }

    eventSource.addEventListener('complete', () => {
      eventSource.close()
      setIsConnected(false)
      options?.onComplete?.()
    })

    eventSource.onerror = () => {
      setError(new Error('SSE connection error'))
      setIsConnected(false)
      eventSource.close()
    }

    return () => {
      eventSource.close()
      setIsConnected(false)
    }
  }, [projectId, runId, addLog])

  return { logs, isConnected, error, clearLogs: handleClearLogs }
}
