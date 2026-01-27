import { http, HttpResponse } from 'msw'
import type { ProjectResponse, FileResponse, DiffScanResponse } from '../api/types'

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
  },
]

export const mockFiles: FileResponse[] = [
  { id: 1, file_path: 'doc1.md', content_hash: 'abc123' },
  { id: 2, file_path: 'doc2.txt', content_hash: 'def456' },
  { id: 3, file_path: 'subdir/doc3.md', content_hash: 'ghi789' },
]

const BASE_URL = 'http://localhost:8000'

export const handlers = [
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
    const body = (await request.json()) as { file_path: string }
    const newFile: FileResponse = {
      id: mockFiles.length + 1,
      file_path: body.file_path,
      content_hash: 'new_hash_' + Date.now(),
    }
    return HttpResponse.json(newFile, { status: 201 })
  }),

  http.delete(`${BASE_URL}/api/projects/:projectId/files/:fileId`, () => {
    return new HttpResponse(null, { status: 204 })
  }),

  http.post(`${BASE_URL}/api/projects/:projectId/files/diff-scan`, () => {
    const response: DiffScanResponse = {
      added: ['new_file.md', 'another_new.txt'],
      modified: ['doc1.md'],
      deleted: [],
    }
    return HttpResponse.json(response)
  }),
]
