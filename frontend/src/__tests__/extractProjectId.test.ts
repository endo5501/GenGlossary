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

  it('should return undefined when Number() produces NaN', () => {
    expect(extractProjectId('/projects/')).toBeUndefined()
  })

  it('should handle large numeric IDs', () => {
    expect(extractProjectId('/projects/999999')).toBe(999999)
  })
})
