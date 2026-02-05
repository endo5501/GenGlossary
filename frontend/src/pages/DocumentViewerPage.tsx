import { useState, useMemo, useEffect } from 'react'
import { Box, Title, Alert, Button, Group } from '@mantine/core'
import { IconAlertCircle } from '@tabler/icons-react'
import { useFiles, useFileDetail } from '../api/hooks/useFiles'
import { useRefined } from '../api/hooks/useRefined'
import { useProvisional } from '../api/hooks/useProvisional'
import { DocumentPane, TermCard } from '../components/document-viewer'
import { findTermData } from '../utils/termUtils'

interface DocumentViewerPageProps {
  projectId: number
  fileId?: number
}

export function DocumentViewerPage({ projectId, fileId }: DocumentViewerPageProps) {
  const [selectedFileId, setSelectedFileId] = useState<number | null>(fileId ?? null)
  const [selectedTerm, setSelectedTerm] = useState<string | null>(null)

  // Fetch data
  const {
    data: files = [],
    isError: isFilesError,
    refetch: refetchFiles,
  } = useFiles(projectId)
  const {
    data: fileDetail,
    isLoading: isFileLoading,
    isError: isFileDetailError,
    error: fileDetailError,
    refetch: refetchFileDetail,
  } = useFileDetail(projectId, selectedFileId ?? undefined)
  const {
    data: refinedTerms = [],
    isError: isRefinedError,
    refetch: refetchRefined,
  } = useRefined(projectId)
  const {
    data: provisionalTerms = [],
    isError: isProvisionalError,
    refetch: refetchProvisional,
  } = useProvisional(projectId)

  // Combined terms error
  const isTermsError = isRefinedError || isProvisionalError
  const handleRetryTerms = () => {
    refetchRefined()
    refetchProvisional()
  }

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

      {isFilesError && (
        <Alert
          icon={<IconAlertCircle size={16} />}
          title="ファイル一覧の取得に失敗しました"
          color="red"
          mb="md"
        >
          <Group>
            <Button variant="outline" size="xs" onClick={() => refetchFiles()}>
              リトライ
            </Button>
          </Group>
        </Alert>
      )}

      {isTermsError && (
        <Alert
          icon={<IconAlertCircle size={16} />}
          title="用語データの取得に失敗しました"
          color="red"
          mb="md"
        >
          <Group>
            <Button variant="outline" size="xs" onClick={handleRetryTerms}>
              リトライ
            </Button>
          </Group>
        </Alert>
      )}

      <Box
        style={{
          display: 'flex',
          height: 'calc(100% - var(--header-height))',
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
            error={isFileDetailError ? (fileDetailError as Error) : null}
            onRetry={() => refetchFileDetail()}
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
