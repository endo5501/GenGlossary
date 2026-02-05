import { useState, useEffect, useRef } from 'react'
import type { LogMessage } from '../types'
import { getBaseUrl } from '../client'
import { useLogStore } from '../../store/logStore'

interface UseLogStreamOptions {
  onComplete?: (projectId: number) => void
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

  // Use ref to always have access to the latest onComplete callback
  // This avoids stale closure issues and prevents unnecessary reconnections
  const onCompleteRef = useRef(options?.onComplete)
  onCompleteRef.current = options?.onComplete

  // Update context when projectId or runId changes (clears logs when either changes)
  useEffect(() => {
    setCurrentContext(projectId, runId ?? null)
  }, [projectId, runId, setCurrentContext])

  useEffect(() => {
    // Use == null to correctly handle runId=0 as valid
    if (runId == null) {
      setIsConnected(false)
      setError(null)  // Clear error when no run is active
      return
    }

    const url = `${getBaseUrl()}/api/projects/${projectId}/runs/${runId}/logs`
    const eventSource = new EventSource(url)

    const disconnect = () => {
      eventSource.close()
      setIsConnected(false)
    }

    const handleOpen = () => {
      setIsConnected(true)
      setError(null)
    }

    const handleMessage = (event: MessageEvent) => {
      const log = parseLogMessage(event)
      if (log) addLog(log)
    }

    const handleComplete = () => {
      disconnect()
      onCompleteRef.current?.(projectId)
    }

    const handleError = () => {
      setError(new Error('SSE connection error'))
      disconnect()
    }

    eventSource.addEventListener('open', handleOpen)
    eventSource.addEventListener('message', handleMessage)
    eventSource.addEventListener('complete', handleComplete)
    eventSource.addEventListener('error', handleError)

    return disconnect  // eventSource.close() handles all cleanup
  }, [projectId, runId, addLog])

  return { logs, isConnected, error, clearLogs }
}
