import { describe, expect, it } from 'vitest'
import { extractProjectId } from '../utils/extractProjectId'

describe('extractProjectId', () => {
  it('should extract project ID from valid path', () => {
    expect(extractProjectId('/projects/1')).toBe(1)
  })

  it('should extract project ID from path with sub-route', () => {
    expect(extractProjectId('/projects/42/files')).toBe(42)
  })

  it('should return undefined for root path', () => {
    expect(extractProjectId('/')).toBeUndefined()
  })

  it('should return undefined for non-project path', () => {
    expect(extractProjectId('/settings')).toBeUndefined()
  })

  it('should return undefined for path with non-numeric segment', () => {
    expect(extractProjectId('/projects/foo')).toBeUndefined()
  })

  it('should return undefined for trailing slash without ID', () => {
    expect(extractProjectId('/projects/')).toBeUndefined()
  })

  it('should return undefined for malformed path with suffix after digits', () => {
    expect(extractProjectId('/projects/123abc')).toBeUndefined()
  })

  it('should return undefined for IDs exceeding Number.MAX_SAFE_INTEGER', () => {
    expect(extractProjectId('/projects/99999999999999999')).toBeUndefined()
  })

  it('should handle large but safe numeric IDs', () => {
    expect(extractProjectId('/projects/999999')).toBe(999999)
  })
})
