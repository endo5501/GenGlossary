import { useState, useMemo, useEffect } from 'react'
import { Box, Title } from '@mantine/core'
import { useFiles, useFileDetail } from '../api/hooks/useFiles'
import { useRefined } from '../api/hooks/useRefined'
import { useProvisional } from '../api/hooks/useProvisional'
import { DocumentPane, TermCard } from '../components/document-viewer'
import type { GlossaryTermResponse } from '../api/types'

interface DocumentViewerPageProps {
  projectId: number
  fileId?: number
}

export function DocumentViewerPage({ projectId, fileId }: DocumentViewerPageProps) {
  const [selectedFileId, setSelectedFileId] = useState<number | null>(fileId ?? null)
  const [selectedTerm, setSelectedTerm] = useState<string | null>(null)

  // Fetch data
  const { data: files = [] } = useFiles(projectId)
  const { data: fileDetail, isLoading: isFileLoading } = useFileDetail(
    projectId,
    selectedFileId ?? undefined
  )
  const { data: refinedTerms = [] } = useRefined(projectId)
  const { data: provisionalTerms = [] } = useProvisional(projectId)

  // Auto-select first file if none selected
  useEffect(() => {
    if (files.length > 0 && selectedFileId === null) {
      setSelectedFileId(files[0].id)
    }
  }, [files, selectedFileId])

  // Clear selected term when file changes
  useEffect(() => {
    setSelectedTerm(null)
  }, [selectedFileId])

  // Extract term texts for highlighting from glossary (not raw extracted terms)
  // Use refined if available, otherwise provisional (both exclude COMMON_NOUN)
  const termTexts = useMemo(
    () =>
      (refinedTerms.length > 0 ? refinedTerms : provisionalTerms).map(
        (t) => t.term_name
      ),
    [refinedTerms, provisionalTerms]
  )

  // Find term data for selected term
  const findTermData = (
    termList: GlossaryTermResponse[],
    termText: string
  ): GlossaryTermResponse | null => {
    return (
      termList.find(
        (t) => t.term_name.toLowerCase() === termText.toLowerCase()
      ) ?? null
    )
  }

  const refinedData = selectedTerm
    ? findTermData(refinedTerms, selectedTerm)
    : null
  const provisionalData = selectedTerm
    ? findTermData(provisionalTerms, selectedTerm)
    : null

  return (
    <Box p="md" h="100%">
      <Title order={2} mb="lg">
        Document Viewer
      </Title>

      <Box
        style={{
          display: 'flex',
          height: 'calc(100% - 60px)',
          gap: 'var(--mantine-spacing-md)',
        }}
      >
        <Box style={{ flex: 7, minWidth: 0, height: '100%' }}>
          <DocumentPane
            files={files}
            selectedFileId={selectedFileId}
            onFileSelect={setSelectedFileId}
            content={fileDetail?.content ?? null}
            isLoading={isFileLoading}
            terms={termTexts}
            selectedTerm={selectedTerm}
            onTermClick={setSelectedTerm}
          />
        </Box>
        <Box style={{ flex: 5, minWidth: 0, height: '100%' }}>
          <TermCard
            selectedTerm={selectedTerm}
            refinedData={refinedData}
            provisionalData={provisionalData}
          />
        </Box>
      </Box>
    </Box>
  )
}
