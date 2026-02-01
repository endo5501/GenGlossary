// Project types
export type ProjectStatus = 'created' | 'running' | 'completed' | 'error'

export interface ProjectResponse {
  id: number
  name: string
  doc_root: string
  llm_provider: string
  llm_model: string
  llm_base_url: string
  created_at: string
  updated_at: string
  last_run_at: string | null
  status: ProjectStatus
  document_count: number
  term_count: number
  issue_count: number
}

export interface ProjectCreateRequest {
  name: string
  doc_root?: string
  llm_provider?: string
  llm_model?: string
  llm_base_url?: string
}

export interface ProjectCloneRequest {
  new_name: string
}

export interface ProjectUpdateRequest {
  name?: string
  llm_provider?: string
  llm_model?: string
  llm_base_url?: string
}

// File types
export interface FileResponse {
  id: number
  file_name: string
  content_hash: string
}

export interface FileDetailResponse {
  id: number
  file_name: string
  content_hash: string
  content: string
}

export interface FileCreateRequest {
  file_name: string
  content: string
}

export interface FileCreateBulkRequest {
  files: FileCreateRequest[]
}

// Term types
export interface TermResponse {
  id: number
  term_text: string
  category: string | null
}

// Term occurrence
export interface TermOccurrence {
  document_path: string
  line_number: number
  context: string
}

// Extended term response with occurrences
export interface TermDetailResponse extends TermResponse {
  occurrences: TermOccurrence[]
}

// Term create/update requests
export interface TermCreateRequest {
  term_text: string
  category?: string
}

export interface TermUpdateRequest {
  term_text?: string
  category?: string
}

// Provisional update request
export interface ProvisionalUpdateRequest {
  definition?: string
  confidence?: number
}

// Log message for SSE stream
export interface LogMessage {
  run_id: number
  level: 'info' | 'warning' | 'error'
  message: string
  timestamp: string
  // Progress-related fields (optional)
  step?: string
  progress_current?: number
  progress_total?: number
  current_term?: string
}

// Run create request
export interface RunCreateRequest {
  scope: RunScope
}

// Glossary types
export interface GlossaryTermResponse {
  id: number
  term_name: string
  definition: string
  confidence: number
  occurrences: TermOccurrence[]
}

// Issue types - matches actual backend response
// Backend Issue Types: unclear, contradiction, missing_relation, unnecessary
export type IssueType = 'unclear' | 'contradiction' | 'missing_relation' | 'unnecessary'

export interface IssueResponse {
  id: number
  term_name: string
  issue_type: IssueType
  description: string
}

// Run types
export type RunScope = 'full' | 'extract' | 'generate' | 'review' | 'refine'
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
  finished_at: string | null
  triggered_by: string
  error_message: string | null
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
