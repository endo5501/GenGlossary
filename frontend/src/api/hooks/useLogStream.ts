import { useState, useEffect, useCallback } from 'react'
import type { LogMessage } from '../types'

const BASE_URL = 'http://localhost:8000'

interface UseLogStreamResult {
  logs: LogMessage[]
  isConnected: boolean
  error: Error | null
  clearLogs: () => void
}

export function useLogStream(
  projectId: number,
  runId: number | undefined
): UseLogStreamResult {
  const [logs, setLogs] = useState<LogMessage[]>([])
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const clearLogs = useCallback(() => {
    setLogs([])
  }, [])

  useEffect(() => {
    if (!runId) {
      setIsConnected(false)
      return
    }

    const url = `${BASE_URL}/api/projects/${projectId}/runs/${runId}/logs`
    let eventSource: EventSource | null = null

    try {
      eventSource = new EventSource(url)

      eventSource.onopen = () => {
        setIsConnected(true)
        setError(null)
      }

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as LogMessage
          setLogs((prev) => [...prev, data])
        } catch {
          // Ignore parse errors
        }
      }

      eventSource.addEventListener('complete', () => {
        eventSource?.close()
        setIsConnected(false)
      })

      eventSource.onerror = () => {
        setError(new Error('SSE connection error'))
        setIsConnected(false)
        eventSource?.close()
      }
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to connect'))
      setIsConnected(false)
    }

    return () => {
      eventSource?.close()
      setIsConnected(false)
    }
  }, [projectId, runId])

  return { logs, isConnected, error, clearLogs }
}
