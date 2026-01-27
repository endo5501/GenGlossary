import { useState, useEffect, useCallback } from 'react'
import type { LogMessage } from '../types'
import { getBaseUrl } from '../client'

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
  runId: number | undefined
): UseLogStreamResult {
  const [logs, setLogs] = useState<LogMessage[]>([])
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const clearLogs = useCallback(() => setLogs([]), [])

  // Clear logs when runId changes
  useEffect(() => {
    setLogs([])
  }, [runId])

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
        const MAX_LOGS = 1000
        setLogs((prev) => {
          const newLogs = [...prev, log]
          return newLogs.length > MAX_LOGS ? newLogs.slice(-MAX_LOGS) : newLogs
        })
      }
    }

    eventSource.addEventListener('complete', () => {
      eventSource.close()
      setIsConnected(false)
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
  }, [projectId, runId])

  return { logs, isConnected, error, clearLogs }
}
