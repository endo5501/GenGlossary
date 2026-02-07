import { http, HttpResponse } from 'msw'
import type {
  ProjectResponse,
  FileResponse,
  TermResponse,
  GlossaryTermResponse,
  IssueResponse,
  RunResponse,
} from '../api/types'

// Mock data
export const mockProjects: ProjectResponse[] = [
  {
    id: 1,
    name: 'Test Project 1',
    doc_root: '/path/to/docs1',
    llm_provider: 'ollama',
    llm_model: 'llama3.2',
    llm_base_url: '',
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-15T10:00:00Z',
    last_run_at: '2024-01-15T12:00:00Z',
    status: 'completed',
    document_count: 5,
    term_count: 20,
    issue_count: 4,
  },
  {
    id: 2,
    name: 'Test Project 2',
    doc_root: '/path/to/docs2',
    llm_provider: 'openai',
    llm_model: 'gpt-4',
    llm_base_url: 'https://api.openai.com/v1',
    created_at: '2024-01-16T10:00:00Z',
    updated_at: '2024-01-16T10:00:00Z',
    last_run_at: null,
    status: 'created',
    document_count: 3,
    term_count: 15,
    issue_count: 0,
  },
]

export const mockFiles: FileResponse[] = [
  { id: 1, file_name: 'doc1.md', content_hash: 'abc123' },
  { id: 2, file_name: 'doc2.txt', content_hash: 'def456' },
  { id: 3, file_name: 'doc3.md', content_hash: 'ghi789' },
]

// Terms mock data - matches actual backend response
export const mockTerms: TermResponse[] = [
  {
    id: 1,
    term_text: '量子コンピュータ',
    category: '技術用語',
  },
  {
    id: 2,
    term_text: '量子ビット',
    category: '技術用語',
  },
  {
    id: 3,
    term_text: '重ね合わせ',
    category: null,
  },
]

// Provisional glossary mock data
export const mockProvisionalEntries: GlossaryTermResponse[] = [
  {
    id: 1,
    term_name: '量子コンピュータ',
    definition: '量子力学の原理を利用して計算を行うコンピュータ。',
    confidence: 0.95,
    occurrences: [
      { document_path: 'doc1.md', line_number: 1, context: '量子コンピュータは...' },
    ],
  },
  {
    id: 2,
    term_name: '量子ビット',
    definition: '量子コンピュータで情報を扱う基本単位。',
    confidence: 0.8,
    occurrences: [
      { document_path: 'doc1.md', line_number: 3, context: '量子ビット（キュービット）を使用します。' },
    ],
  },
]

// Issues mock data - matches actual backend response
// Backend Issue Types: unclear, contradiction, missing_relation, unnecessary
export const mockIssues: IssueResponse[] = [
  {
    id: 1,
    term_name: '量子コンピュータ',
    issue_type: 'unclear',
    description: '「量子コンピュータ」の定義が曖昧です。',
  },
  {
    id: 2,
    term_name: '量子ビット',
    issue_type: 'contradiction',
    description: '「量子ビット」と「キュービット」の使い分けが不明確です。',
  },
  {
    id: 3,
    term_name: '量子もつれ',
    issue_type: 'missing_relation',
    description: '「量子もつれ」の定義が不足しています。',
  },
  {
    id: 4,
    term_name: '量子アルゴリズム',
    issue_type: 'unnecessary',
    description: '「量子アルゴリズム」は用語集に不要です。',
  },
]

// Refined glossary mock data
export const mockRefinedEntries: GlossaryTermResponse[] = [
  {
    id: 1,
    term_name: '量子コンピュータ',
    definition: '量子力学の原理（重ね合わせ、量子もつれ）を利用して計算を行うコンピュータ。従来のコンピュータとは異なり、量子ビットを使用する。',
    confidence: 0.98,
    occurrences: [
      { document_path: 'doc1.md', line_number: 1, context: '量子コンピュータは...' },
      { document_path: 'doc1.md', line_number: 5, context: '量子コンピュータの最大の特徴は...' },
    ],
  },
]

// Run mock data
export const mockCurrentRun: RunResponse = {
  id: 0,
  scope: 'full',
  status: 'pending',
  progress_current: 0,
  progress_total: 0,
  current_step: null,
  created_at: '2024-01-15T10:00:00Z',
  started_at: null,
  finished_at: null,
  triggered_by: 'manual',
  error_message: null,
}

const BASE_URL = 'http://localhost:8000'

export const handlers = [
  // Ollama
  http.get(`${BASE_URL}/api/ollama/models`, () => {
    return HttpResponse.json({
      models: [
        { name: 'llama2' },
        { name: 'llama3.2' },
        { name: 'codellama' },
      ],
    })
  }),

  // Projects
  http.get(`${BASE_URL}/api/projects`, () => {
    return HttpResponse.json(mockProjects)
  }),

  http.get(`${BASE_URL}/api/projects/:id`, ({ params }) => {
    const id = Number(params.id)
    const project = mockProjects.find((p) => p.id === id)
    if (!project) {
      return HttpResponse.json({ detail: 'Not found' }, { status: 404 })
    }
    return HttpResponse.json(project)
  }),

  http.post(`${BASE_URL}/api/projects`, async ({ request }) => {
    const body = (await request.json()) as { name: string; doc_root: string; llm_base_url?: string }
    const newProject: ProjectResponse = {
      id: mockProjects.length + 1,
      name: body.name,
      doc_root: body.doc_root,
      llm_provider: 'ollama',
      llm_model: '',
      llm_base_url: body.llm_base_url ?? '',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      last_run_at: null,
      status: 'created',
      document_count: 0,
      term_count: 0,
      issue_count: 0,
    }
    return HttpResponse.json(newProject, { status: 201 })
  }),

  http.post(`${BASE_URL}/api/projects/:id/clone`, async ({ params, request }) => {
    const id = Number(params.id)
    const source = mockProjects.find((p) => p.id === id)
    if (!source) {
      return HttpResponse.json({ detail: 'Not found' }, { status: 404 })
    }
    const body = (await request.json()) as { new_name: string }
    const cloned: ProjectResponse = {
      id: mockProjects.length + 1,
      name: body.new_name,
      doc_root: source.doc_root,
      llm_provider: source.llm_provider,
      llm_model: source.llm_model,
      llm_base_url: source.llm_base_url,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      last_run_at: null,
      status: 'created',
      document_count: source.document_count,
      term_count: source.term_count,
      issue_count: source.issue_count,
    }
    return HttpResponse.json(cloned, { status: 201 })
  }),

  http.delete(`${BASE_URL}/api/projects/:id`, ({ params }) => {
    const id = Number(params.id)
    const project = mockProjects.find((p) => p.id === id)
    if (!project) {
      return HttpResponse.json({ detail: 'Not found' }, { status: 404 })
    }
    return new HttpResponse(null, { status: 204 })
  }),

  http.patch(`${BASE_URL}/api/projects/:id`, async ({ params, request }) => {
    const id = Number(params.id)
    const project = mockProjects.find((p) => p.id === id)
    if (!project) {
      return HttpResponse.json({ detail: 'Not found' }, { status: 404 })
    }
    const body = (await request.json()) as {
      name?: string
      llm_provider?: string
      llm_model?: string
      llm_base_url?: string
    }

    // Check for duplicate name
    if (body.name) {
      const existingWithName = mockProjects.find((p) => p.name === body.name && p.id !== id)
      if (existingWithName) {
        return HttpResponse.json({ detail: `Project name already exists: ${body.name}` }, { status: 409 })
      }
    }

    const updated: ProjectResponse = {
      ...project,
      name: body.name ?? project.name,
      llm_provider: body.llm_provider ?? project.llm_provider,
      llm_model: body.llm_model ?? project.llm_model,
      llm_base_url: body.llm_base_url ?? project.llm_base_url,
      updated_at: new Date().toISOString(),
    }
    return HttpResponse.json(updated)
  }),

  // Files
  http.get(`${BASE_URL}/api/projects/:projectId/files`, () => {
    return HttpResponse.json(mockFiles)
  }),

  http.post(`${BASE_URL}/api/projects/:projectId/files`, async ({ request }) => {
    const body = (await request.json()) as { file_name: string; content: string }
    const newFile: FileResponse = {
      id: mockFiles.length + 1,
      file_name: body.file_name,
      content_hash: 'new_hash_' + Date.now(),
    }
    return HttpResponse.json(newFile, { status: 201 })
  }),

  http.post(`${BASE_URL}/api/projects/:projectId/files/bulk`, async ({ request }) => {
    const body = (await request.json()) as { files: { file_name: string; content: string }[] }
    const newFiles: FileResponse[] = body.files.map((f, idx) => ({
      id: mockFiles.length + idx + 1,
      file_name: f.file_name,
      content_hash: 'new_hash_' + Date.now() + idx,
    }))
    return HttpResponse.json(
      { files: newFiles, extract_started: true, extract_skipped_reason: null },
      { status: 201 }
    )
  }),

  http.delete(`${BASE_URL}/api/projects/:projectId/files/:fileId`, () => {
    return new HttpResponse(null, { status: 204 })
  }),

  // Terms
  http.get(`${BASE_URL}/api/projects/:projectId/terms`, () => {
    return HttpResponse.json(mockTerms)
  }),

  http.get(`${BASE_URL}/api/projects/:projectId/terms/:termId`, ({ params }) => {
    const term = mockTerms.find((t) => t.id === Number(params.termId))
    if (!term) {
      return HttpResponse.json({ detail: 'Not found' }, { status: 404 })
    }
    return HttpResponse.json(term)
  }),

  http.post(`${BASE_URL}/api/projects/:projectId/terms`, async ({ request }) => {
    const body = (await request.json()) as { term_text: string; category?: string }
    const newTerm: TermResponse = {
      id: mockTerms.length + 1,
      term_text: body.term_text,
      category: body.category ?? null,
    }
    return HttpResponse.json(newTerm, { status: 201 })
  }),

  http.patch(`${BASE_URL}/api/projects/:projectId/terms/:termId`, async ({ params, request }) => {
    const term = mockTerms.find((t) => t.id === Number(params.termId))
    if (!term) {
      return HttpResponse.json({ detail: 'Not found' }, { status: 404 })
    }
    const body = (await request.json()) as { term_text?: string; category?: string }
    return HttpResponse.json({ ...term, ...body })
  }),

  http.delete(`${BASE_URL}/api/projects/:projectId/terms/:termId`, () => {
    return new HttpResponse(null, { status: 204 })
  }),

  http.post(`${BASE_URL}/api/projects/:projectId/terms/extract`, () => {
    return HttpResponse.json({ message: 'Extraction started' }, { status: 202 })
  }),

  // Provisional
  http.get(`${BASE_URL}/api/projects/:projectId/provisional`, () => {
    return HttpResponse.json(mockProvisionalEntries)
  }),

  http.get(`${BASE_URL}/api/projects/:projectId/provisional/:entryId`, ({ params }) => {
    const entry = mockProvisionalEntries.find((e) => e.id === Number(params.entryId))
    if (!entry) {
      return HttpResponse.json({ detail: 'Not found' }, { status: 404 })
    }
    return HttpResponse.json(entry)
  }),

  http.patch(`${BASE_URL}/api/projects/:projectId/provisional/:entryId`, async ({ params, request }) => {
    const entry = mockProvisionalEntries.find((e) => e.id === Number(params.entryId))
    if (!entry) {
      return HttpResponse.json({ detail: 'Not found' }, { status: 404 })
    }
    const body = (await request.json()) as { definition?: string; confidence?: number }
    return HttpResponse.json({ ...entry, ...body })
  }),

  http.post(`${BASE_URL}/api/projects/:projectId/provisional/regenerate`, () => {
    return HttpResponse.json({ message: 'Regeneration started' }, { status: 202 })
  }),

  // Issues
  http.get(`${BASE_URL}/api/projects/:projectId/issues`, ({ request }) => {
    const url = new URL(request.url)
    const issueType = url.searchParams.get('issue_type')
    if (issueType) {
      return HttpResponse.json(mockIssues.filter((i) => i.issue_type === issueType))
    }
    return HttpResponse.json(mockIssues)
  }),

  http.get(`${BASE_URL}/api/projects/:projectId/issues/:issueId`, ({ params }) => {
    const issue = mockIssues.find((i) => i.id === Number(params.issueId))
    if (!issue) {
      return HttpResponse.json({ detail: 'Not found' }, { status: 404 })
    }
    return HttpResponse.json(issue)
  }),

  http.post(`${BASE_URL}/api/projects/:projectId/issues/review`, () => {
    return HttpResponse.json({ message: 'Review started' }, { status: 202 })
  }),

  // Refined
  http.get(`${BASE_URL}/api/projects/:projectId/refined`, () => {
    return HttpResponse.json(mockRefinedEntries)
  }),

  http.get(`${BASE_URL}/api/projects/:projectId/refined/:termId`, ({ params }) => {
    const entry = mockRefinedEntries.find((e) => e.id === Number(params.termId))
    if (!entry) {
      return HttpResponse.json({ detail: 'Not found' }, { status: 404 })
    }
    return HttpResponse.json(entry)
  }),

  http.get(`${BASE_URL}/api/projects/:projectId/refined/export`, () => {
    const markdown = `# 用語集\n\n## 量子コンピュータ\n量子力学の原理を利用して計算を行うコンピュータ。`
    return new HttpResponse(markdown, {
      headers: { 'Content-Type': 'text/markdown' },
    })
  }),

  http.post(`${BASE_URL}/api/projects/:projectId/refined/regenerate`, () => {
    return HttpResponse.json({ message: 'Regeneration started' }, { status: 202 })
  }),

  // Runs
  http.get(`${BASE_URL}/api/projects/:projectId/runs/current`, () => {
    return HttpResponse.json(mockCurrentRun)
  }),

  http.post(`${BASE_URL}/api/projects/:projectId/runs`, async ({ request }) => {
    const body = (await request.json()) as { scope: string }
    const newRun: RunResponse = {
      id: 1,
      scope: body.scope as RunResponse['scope'],
      status: 'running',
      progress_current: 0,
      progress_total: 4,
      current_step: 'extracting_terms',
      created_at: new Date().toISOString(),
      started_at: new Date().toISOString(),
      finished_at: null,
      triggered_by: 'manual',
      error_message: null,
    }
    return HttpResponse.json(newRun, { status: 201 })
  }),

  http.delete(`${BASE_URL}/api/projects/:projectId/runs/:runId`, () => {
    return HttpResponse.json({ message: 'Run cancelled' })
  }),
]
