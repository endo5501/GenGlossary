// File types
export interface FileResponse {
  id: number
  file_path: string
  content_hash: string
}

// Term types
export interface TermResponse {
  id: number
  term_text: string
  category: string | null
}

// Term occurrence
export interface TermOccurrence {
  line_number: number
  context: string
}

// Glossary types
export interface GlossaryTermResponse {
  id: number
  term_name: string
  definition: string
  confidence: number
  occurrences: TermOccurrence[]
}

// Issue types
export interface IssueResponse {
  id: number
  term_id: number | null
  issue_type: string
  description: string
  severity: 'low' | 'medium' | 'high'
}

// Run types
export type RunScope = 'full' | 'from_terms' | 'provisional_to_refined'
export type RunStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'

export interface RunResponse {
  id: number
  scope: RunScope
  status: RunStatus
  progress_current: number
  progress_total: number
  current_step: string | null
  created_at: string
  started_at: string | null
  completed_at: string | null
}

// Settings types
export interface SettingsResponse {
  id: number
  model_name: string
  ollama_base_url: string
  max_retries: number
  timeout_seconds: number
}

// API response wrappers
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  per_page: number
}

export interface ErrorResponse {
  detail: string
}
