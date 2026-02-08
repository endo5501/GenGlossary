import { describe, expect, it, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MantineProvider } from '@mantine/core'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { server } from './setup'
import { handlers } from '../mocks/handlers'
import { http, HttpResponse } from 'msw'
import { DocumentViewerPage } from '../pages/DocumentViewerPage'
import type {
  TermResponse,
  GlossaryTermResponse,
  FileResponse,
  FileDetailResponse,
} from '../api/types'

const BASE_URL = 'http://localhost:8000'

// Mock files data
const mockFiles: FileResponse[] = [
  { id: 1, file_name: 'test.md', file_path: '/test.md' },
]

const mockFileDetail: FileDetailResponse = {
  id: 1,
  file_name: 'test.md',
  file_path: '/test.md',
  content: '量子コンピュータは量子力学を利用します。計算機は一般名詞です。',
}

// Terms for COMMON_NOUN test - uses 計算機 instead of コンピュータ to avoid partial match
const mockTermsWithCommonNoun: TermResponse[] = [
  { id: 1, term_text: '量子コンピュータ', category: '技術用語' },
  { id: 2, term_text: '量子力学', category: '技術用語' },
  { id: 3, term_text: '計算機', category: 'COMMON_NOUN' }, // Should NOT be highlighted
]


// Provisional glossary - only processed terms (no COMMON_NOUN)
const mockProvisionalTerms: GlossaryTermResponse[] = [
  {
    id: 1,
    term_name: '量子コンピュータ',
    definition: '量子力学の原理を利用したコンピュータ',
    confidence: 0.9,
    occurrences: [{ document_path: 'test.md', line_number: 1, context: '量子コンピュータは...' }],
  },
  {
    id: 2,
    term_name: '量子力学',
    definition: '物理学の一分野',
    confidence: 0.85,
    occurrences: [{ document_path: 'test.md', line_number: 1, context: '量子力学を利用' }],
  },
]

// Refined glossary
const mockRefinedTerms: GlossaryTermResponse[] = [
  {
    id: 1,
    term_name: '量子コンピュータ',
    definition: '量子力学の原理を利用した次世代コンピュータ',
    confidence: 0.95,
    occurrences: [{ document_path: 'test.md', line_number: 1, context: '量子コンピュータは...' }],
  },
]

// Refined glossary with aliases
const mockRefinedTermsWithAliases: GlossaryTermResponse[] = [
  {
    id: 1,
    term_name: '量子コンピュータ',
    definition: '量子力学の原理を利用した次世代コンピュータ',
    confidence: 0.95,
    occurrences: [{ document_path: 'test.md', line_number: 1, context: '量子コンピュータは...' }],
    aliases: ['量子計算機'],
  },
]

const mockFileDetailWithAliases: FileDetailResponse = {
  id: 1,
  file_name: 'test.md',
  file_path: '/test.md',
  content: '量子コンピュータは量子力学を利用します。量子計算機とも呼ばれます。',
}

// Mock react-router
vi.mock('@tanstack/react-router', async () => {
  const actual = await vi.importActual('@tanstack/react-router')
  return {
    ...actual,
    useNavigate: () => vi.fn(),
    Link: ({ children, to, ...props }: { children: React.ReactNode; to: string; [key: string]: unknown }) => (
      <a href={to} {...props}>{children}</a>
    ),
  }
})

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  })

  return {
    ...render(
      <QueryClientProvider client={queryClient}>
        <MantineProvider>{ui}</MantineProvider>
      </QueryClientProvider>
    ),
  }
}

// Base handlers for files API
const filesHandlers = [
  http.get(`${BASE_URL}/api/projects/:projectId/files`, () => {
    return HttpResponse.json(mockFiles)
  }),
  http.get(`${BASE_URL}/api/projects/:projectId/files/:fileId`, () => {
    return HttpResponse.json(mockFileDetail)
  }),
]

// Runs handler (idle state)
const runsHandler = http.get(`${BASE_URL}/api/projects/:projectId/runs/current`, () => {
  return HttpResponse.json({
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
  })
})

describe('DocumentViewerPage - Term Highlighting Filter', () => {
  beforeEach(() => {
    server.use(...handlers, ...filesHandlers, runsHandler)
  })

  describe('when refinedTerms exist', () => {
    beforeEach(() => {
      server.use(
        http.get(`${BASE_URL}/api/projects/:projectId/terms`, () => {
          return HttpResponse.json(mockTermsWithCommonNoun)
        }),
        http.get(`${BASE_URL}/api/projects/:projectId/provisional`, () => {
          return HttpResponse.json(mockProvisionalTerms)
        }),
        http.get(`${BASE_URL}/api/projects/:projectId/refined`, () => {
          return HttpResponse.json(mockRefinedTerms)
        })
      )
    })

    it('highlights only terms from refinedTerms, not COMMON_NOUN', async () => {
      renderWithProviders(<DocumentViewerPage projectId={1} />)

      // Wait for content to load
      await waitFor(() => {
        expect(screen.getByText(/量子コンピュータ/)).toBeInTheDocument()
      })

      // Find highlighted terms (background color indicates highlighting)
      const highlightedElements = document.querySelectorAll('[style*="background"]')
      const highlightedTexts = Array.from(highlightedElements).map(el => el.textContent)

      // '量子コンピュータ' should be highlighted (in refinedTerms)
      expect(highlightedTexts).toContain('量子コンピュータ')

      // '計算機' should NOT be highlighted (COMMON_NOUN, not in refined)
      expect(highlightedTexts).not.toContain('計算機')

      // '量子力学' should NOT be highlighted (not in refinedTerms, only in provisional)
      expect(highlightedTexts).not.toContain('量子力学')

      // Only 1 term should be highlighted (量子コンピュータ)
      expect(highlightedElements.length).toBe(1)
    })
  })

  describe('when only provisionalTerms exist (no refined)', () => {
    beforeEach(() => {
      server.use(
        http.get(`${BASE_URL}/api/projects/:projectId/terms`, () => {
          return HttpResponse.json(mockTermsWithCommonNoun)
        }),
        http.get(`${BASE_URL}/api/projects/:projectId/provisional`, () => {
          return HttpResponse.json(mockProvisionalTerms)
        }),
        http.get(`${BASE_URL}/api/projects/:projectId/refined`, () => {
          return HttpResponse.json([]) // Empty refined
        })
      )
    })

    it('highlights terms from provisionalTerms, not COMMON_NOUN', async () => {
      renderWithProviders(<DocumentViewerPage projectId={1} />)

      // Wait for content to load
      await waitFor(() => {
        expect(screen.getByText(/量子コンピュータ/)).toBeInTheDocument()
      })

      // Find highlighted terms
      const highlightedElements = document.querySelectorAll('[style*="background"]')
      const highlightedTexts = Array.from(highlightedElements).map(el => el.textContent)

      // '量子コンピュータ' and '量子力学' should be highlighted (in provisionalTerms)
      expect(highlightedTexts).toContain('量子コンピュータ')
      expect(highlightedTexts).toContain('量子力学')

      // '計算機' should NOT be highlighted (COMMON_NOUN)
      expect(highlightedTexts).not.toContain('計算機')

      // Only 2 terms should be highlighted
      expect(highlightedElements.length).toBe(2)
    })
  })

  describe('when no glossary terms exist', () => {
    beforeEach(() => {
      server.use(
        http.get(`${BASE_URL}/api/projects/:projectId/terms`, () => {
          return HttpResponse.json(mockTermsWithCommonNoun)
        }),
        http.get(`${BASE_URL}/api/projects/:projectId/provisional`, () => {
          return HttpResponse.json([])
        }),
        http.get(`${BASE_URL}/api/projects/:projectId/refined`, () => {
          return HttpResponse.json([])
        })
      )
    })

    it('does not highlight any terms', async () => {
      renderWithProviders(<DocumentViewerPage projectId={1} />)

      // Wait for content to load
      await waitFor(() => {
        expect(screen.getByText(/量子コンピュータは量子力学を利用します/)).toBeInTheDocument()
      })

      // No highlighted elements should exist
      const highlightedElements = document.querySelectorAll('[style*="background"]')
      expect(highlightedElements.length).toBe(0)
    })
  })
})

describe('DocumentViewerPage - Alias Highlighting', () => {
  beforeEach(() => {
    server.use(
      ...handlers,
      ...filesHandlers,
      runsHandler,
      http.get(`${BASE_URL}/api/projects/:projectId/terms`, () => {
        return HttpResponse.json(mockTermsWithCommonNoun)
      }),
      http.get(`${BASE_URL}/api/projects/:projectId/provisional`, () => {
        return HttpResponse.json([])
      }),
      http.get(`${BASE_URL}/api/projects/:projectId/refined`, () => {
        return HttpResponse.json(mockRefinedTermsWithAliases)
      }),
      http.get(`${BASE_URL}/api/projects/:projectId/files/:fileId`, () => {
        return HttpResponse.json(mockFileDetailWithAliases)
      })
    )
  })

  it('highlights aliases in addition to term names', async () => {
    renderWithProviders(<DocumentViewerPage projectId={1} />)

    await waitFor(() => {
      expect(screen.getByText(/量子コンピュータ/)).toBeInTheDocument()
    })

    const highlightedElements = document.querySelectorAll('[style*="background"]')
    const highlightedTexts = Array.from(highlightedElements).map(el => el.textContent)

    // Both term_name and alias should be highlighted
    expect(highlightedTexts).toContain('量子コンピュータ')
    expect(highlightedTexts).toContain('量子計算機')
  })

  it('selects representative term when alias is clicked', async () => {
    renderWithProviders(<DocumentViewerPage projectId={1} />)

    await waitFor(() => {
      expect(screen.getByText(/量子計算機/)).toBeInTheDocument()
    })

    // Click the alias text
    const highlightedElements = document.querySelectorAll('[style*="background"]')
    const aliasElement = Array.from(highlightedElements).find(
      el => el.textContent === '量子計算機'
    )
    expect(aliasElement).toBeDefined()
    ;(aliasElement as HTMLElement).click()

    // After clicking alias, the representative term '量子コンピュータ' should be selected
    // which means both the term and alias should show selected color (#ffeb3b)
    await waitFor(() => {
      const updatedElements = document.querySelectorAll('[style*="background"]')
      const termElement = Array.from(updatedElements).find(
        el => el.textContent === '量子コンピュータ'
      )
      expect(termElement).toBeDefined()
      expect((termElement as HTMLElement).style.backgroundColor).toBe('rgb(255, 235, 59)')
    })
  })

  it('highlights alias with selected color when representative term is selected', async () => {
    renderWithProviders(<DocumentViewerPage projectId={1} />)

    await waitFor(() => {
      expect(screen.getByText(/量子コンピュータ/)).toBeInTheDocument()
    })

    // Click the representative term
    const highlightedElements = document.querySelectorAll('[style*="background"]')
    const termElement = Array.from(highlightedElements).find(
      el => el.textContent === '量子コンピュータ'
    )
    ;(termElement as HTMLElement).click()

    // After clicking representative term, alias should also show selected color
    await waitFor(() => {
      const updatedElements = document.querySelectorAll('[style*="background"]')
      const aliasElement = Array.from(updatedElements).find(
        el => el.textContent === '量子計算機'
      )
      expect(aliasElement).toBeDefined()
      expect((aliasElement as HTMLElement).style.backgroundColor).toBe('rgb(255, 235, 59)')
    })
  })
})

describe('DocumentViewerPage - Error Handling', () => {
  beforeEach(() => {
    server.use(...handlers, runsHandler)
  })

  describe('when files API fails', () => {
    beforeEach(() => {
      server.use(
        http.get(`${BASE_URL}/api/projects/:projectId/files`, () => {
          return HttpResponse.json({ detail: 'Server error' }, { status: 500 })
        }),
        http.get(`${BASE_URL}/api/projects/:projectId/provisional`, () => {
          return HttpResponse.json([])
        }),
        http.get(`${BASE_URL}/api/projects/:projectId/refined`, () => {
          return HttpResponse.json([])
        })
      )
    })

    it('displays error alert with retry button', async () => {
      renderWithProviders(<DocumentViewerPage projectId={1} />)

      await waitFor(() => {
        expect(screen.getByText(/ファイル一覧/)).toBeInTheDocument()
      })

      expect(screen.getByRole('button', { name: /リトライ/i })).toBeInTheDocument()
    })
  })

  describe('when file detail API fails', () => {
    beforeEach(() => {
      server.use(
        ...filesHandlers.slice(0, 1), // Only list files handler
        http.get(`${BASE_URL}/api/projects/:projectId/files/:fileId`, () => {
          return HttpResponse.json({ detail: 'File not found' }, { status: 404 })
        }),
        http.get(`${BASE_URL}/api/projects/:projectId/provisional`, () => {
          return HttpResponse.json([])
        }),
        http.get(`${BASE_URL}/api/projects/:projectId/refined`, () => {
          return HttpResponse.json([])
        })
      )
    })

    it('displays error in document pane with retry button', async () => {
      renderWithProviders(<DocumentViewerPage projectId={1} />)

      await waitFor(() => {
        expect(screen.getByText(/ファイルの読み込み/)).toBeInTheDocument()
      })

      // Retry button should be in the document pane area
      expect(screen.getByRole('button', { name: /リトライ/i })).toBeInTheDocument()
    })
  })

  describe('when terms API fails', () => {
    beforeEach(() => {
      server.use(
        ...filesHandlers,
        http.get(`${BASE_URL}/api/projects/:projectId/provisional`, () => {
          return HttpResponse.json({ detail: 'Server error' }, { status: 500 })
        }),
        http.get(`${BASE_URL}/api/projects/:projectId/refined`, () => {
          return HttpResponse.json({ detail: 'Server error' }, { status: 500 })
        })
      )
    })

    it('displays error alert for terms with retry button', async () => {
      renderWithProviders(<DocumentViewerPage projectId={1} />)

      await waitFor(() => {
        expect(screen.getByText(/用語データ/)).toBeInTheDocument()
      })

      expect(screen.getByRole('button', { name: /リトライ/i })).toBeInTheDocument()
    })
  })
})
