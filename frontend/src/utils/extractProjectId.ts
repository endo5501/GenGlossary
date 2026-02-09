export function extractProjectId(pathname: string): number | undefined {
  const match = pathname.match(/^\/projects\/(\d+)/)
  if (!match) return undefined
  const id = Number(match[1])
  return Number.isFinite(id) ? id : undefined
}
