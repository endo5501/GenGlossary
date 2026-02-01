import { useState, useMemo, useEffect } from 'react'
import { Box, Title, Grid } from '@mantine/core'
import { useFiles, useFileDetail } from '../api/hooks/useFiles'
import { useTerms } from '../api/hooks/useTerms'
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
  const { data: terms = [] } = useTerms(projectId)
  const { data: refinedTerms = [] } = useRefined(projectId)
  const { data: provisionalTerms = [] } = useProvisional(projectId)

  // Auto-select first file if none selected
  useEffect(() => {
    if (files.length > 0 && selectedFileId === null) {
      setSelectedFileId(files[0].id)
    }
  }, [files, selectedFileId])

  // Extract term texts for highlighting
  const termTexts = useMemo(() => terms.map((t) => t.term_text), [terms])

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

      <Grid h="calc(100% - 60px)" gutter="md">
        <Grid.Col span={7}>
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
        </Grid.Col>
        <Grid.Col span={5}>
          <TermCard
            selectedTerm={selectedTerm}
            refinedData={refinedData}
            provisionalData={provisionalData}
          />
        </Grid.Col>
      </Grid>
    </Box>
  )
}
