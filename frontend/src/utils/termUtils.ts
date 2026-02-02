import type { GlossaryTermResponse } from '../api/types'

/**
 * Find term data by term text (case-insensitive match).
 */
export function findTermData(
  termList: GlossaryTermResponse[],
  termText: string
): GlossaryTermResponse | null {
  return (
    termList.find(
      (t) => t.term_name.toLowerCase() === termText.toLowerCase()
    ) ?? null
  )
}
