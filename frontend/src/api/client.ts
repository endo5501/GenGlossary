export class ApiError extends Error {
  status: number
  detail?: string

  constructor(message: string, status: number, detail?: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

export function getBaseUrl(): string {
  const envUrl = import.meta.env.VITE_API_BASE_URL
  if (!envUrl || envUrl === 'undefined') {
    return 'http://localhost:8000'
  }
  return envUrl
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let detail = 'Unknown error'
    try {
      const errorData = await response.json()
      detail = errorData.detail || errorData.message || 'Request failed'
    } catch {
      detail = response.statusText
    }
    throw new ApiError(`Request failed: ${response.status}`, response.status, detail)
  }
  // 204 No Content or empty body
  if (response.status === 204 || response.headers.get('content-length') === '0') {
    return undefined as T
  }
  return response.json()
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${getBaseUrl()}${endpoint}`
  const headers = new Headers(options.headers)
  if (options.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    })
    return handleResponse<T>(response)
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    throw new ApiError(
      error instanceof Error ? error.message : 'Network error',
      0
    )
  }
}

// DRY helper for POST/PUT/PATCH methods
const createDataMethod = (method: string) =>
  <T>(endpoint: string, data?: unknown): Promise<T> =>
    request<T>(endpoint, {
      method,
      body: data !== undefined ? JSON.stringify(data) : undefined,
    })

export const apiClient = {
  get: <T>(endpoint: string): Promise<T> => request<T>(endpoint, { method: 'GET' }),
  post: createDataMethod('POST'),
  put: createDataMethod('PUT'),
  patch: createDataMethod('PATCH'),
  delete: <T>(endpoint: string): Promise<T> => request<T>(endpoint, { method: 'DELETE' }),
}
