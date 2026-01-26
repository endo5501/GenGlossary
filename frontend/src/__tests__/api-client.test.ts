import { describe, expect, it, afterEach } from 'vitest'
import { http, HttpResponse } from 'msw'
import { server } from './setup'
import { apiClient, getBaseUrl, ApiError } from '../api/client'

describe('API Client', () => {
  describe('getBaseUrl', () => {
    const originalEnv = import.meta.env.VITE_API_BASE_URL

    afterEach(() => {
      // Restore original env
      import.meta.env.VITE_API_BASE_URL = originalEnv
    })

    it('should return base URL from environment variable', () => {
      import.meta.env.VITE_API_BASE_URL = 'http://custom-api.example.com'
      expect(getBaseUrl()).toBe('http://custom-api.example.com')
    })

    it('should return default localhost:8000 when env var is not set', () => {
      // Simulate undefined env var (Vite converts to string "undefined")
      import.meta.env.VITE_API_BASE_URL = 'undefined'
      expect(getBaseUrl()).toBe('http://localhost:8000')
    })

    it('should return default localhost:8000 when env var is empty string', () => {
      import.meta.env.VITE_API_BASE_URL = ''
      expect(getBaseUrl()).toBe('http://localhost:8000')
    })
  })

  describe('apiClient', () => {
    it('should make GET requests with correct headers', async () => {
      let capturedHeaders: Headers | null = null

      server.use(
        http.get('http://localhost:8000/api/test', ({ request }) => {
          capturedHeaders = new Headers(request.headers)
          return HttpResponse.json({ success: true })
        })
      )

      await apiClient.get('/api/test')

      expect(capturedHeaders?.get('Content-Type')).toBe('application/json')
    })

    it('should make POST requests with JSON body', async () => {
      let capturedBody: unknown = null

      server.use(
        http.post('http://localhost:8000/api/test', async ({ request }) => {
          capturedBody = await request.json()
          return HttpResponse.json({ success: true })
        })
      )

      await apiClient.post('/api/test', { data: 'test' })

      expect(capturedBody).toEqual({ data: 'test' })
    })

    it('should handle successful responses', async () => {
      server.use(
        http.get('http://localhost:8000/api/test', () => {
          return HttpResponse.json({ message: 'Hello' })
        })
      )

      const result = await apiClient.get<{ message: string }>('/api/test')

      expect(result).toEqual({ message: 'Hello' })
    })

    it('should throw ApiError on 4xx responses', async () => {
      server.use(
        http.get('http://localhost:8000/api/test', () => {
          return HttpResponse.json(
            { detail: 'Not found' },
            { status: 404 }
          )
        })
      )

      await expect(apiClient.get('/api/test')).rejects.toThrow(ApiError)
      await expect(apiClient.get('/api/test')).rejects.toMatchObject({
        status: 404,
        message: 'Not found',
      })
    })

    it('should throw ApiError on 5xx responses', async () => {
      server.use(
        http.get('http://localhost:8000/api/test', () => {
          return HttpResponse.json(
            { detail: 'Internal server error' },
            { status: 500 }
          )
        })
      )

      await expect(apiClient.get('/api/test')).rejects.toThrow(ApiError)
      await expect(apiClient.get('/api/test')).rejects.toMatchObject({
        status: 500,
      })
    })

    it('should throw ApiError on network errors', async () => {
      server.use(
        http.get('http://localhost:8000/api/test', () => {
          return HttpResponse.error()
        })
      )

      await expect(apiClient.get('/api/test')).rejects.toThrow(ApiError)
    })

    it('should handle 204 No Content responses', async () => {
      server.use(
        http.delete('http://localhost:8000/api/test', () => {
          return new HttpResponse(null, { status: 204 })
        })
      )

      const result = await apiClient.delete('/api/test')

      expect(result).toBeUndefined()
    })

    it('should handle empty body with content-length 0', async () => {
      server.use(
        http.post('http://localhost:8000/api/test', () => {
          return new HttpResponse(null, {
            status: 200,
            headers: { 'content-length': '0' },
          })
        })
      )

      const result = await apiClient.post('/api/test', { data: 'test' })

      expect(result).toBeUndefined()
    })
  })
})
