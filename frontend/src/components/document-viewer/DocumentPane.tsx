import { useMemo } from 'react'
import { Tabs, Text, Paper, ScrollArea, Loader, Center } from '@mantine/core'
import { IconFile } from '@tabler/icons-react'
import type { FileResponse } from '../../api/types'

interface DocumentPaneProps {
  files: FileResponse[]
  selectedFileId: number | null
  onFileSelect: (fileId: number) => void
  content: string | null
  isLoading: boolean
  terms: string[]
  selectedTerm: string | null
  onTermClick: (term: string) => void
}

export function DocumentPane({
  files,
  selectedFileId,
  onFileSelect,
  content,
  isLoading,
  terms,
  selectedTerm,
  onTermClick,
}: DocumentPaneProps) {
  // Memoize term set for O(1) lookup (normalized to lowercase)
  const termSet = useMemo(
    () => new Set(terms.map((t) => t.toLowerCase())),
    [terms]
  )

  // Memoize regex pattern to avoid rebuilding on every render
  const termPattern = useMemo(() => {
    const validTerms = terms.filter((t) => t.trim().length > 0)
    if (validTerms.length === 0) return null

    const escapedTerms = validTerms
      .map((t) => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
      .sort((a, b) => b.length - a.length)

    return new RegExp(`(${escapedTerms.join('|')})`, 'gi')
  }, [terms])

  const renderHighlightedContent = (text: string) => {
    if (!termPattern) {
      return <Text style={{ whiteSpace: 'pre-wrap' }}>{text}</Text>
    }

    const parts = text.split(termPattern)

    return (
      <Text style={{ whiteSpace: 'pre-wrap' }}>
        {parts.map((part, index) => {
          // O(1) lookup instead of O(n) linear search
          const isTermMatch = termSet.has(part.toLowerCase())
          if (isTermMatch) {
            const isSelected =
              selectedTerm?.toLowerCase() === part.toLowerCase()
            return (
              <Text
                key={index}
                component="span"
                style={{
                  backgroundColor: isSelected ? '#ffeb3b' : '#e3f2fd',
                  cursor: 'pointer',
                  padding: '0 2px',
                  borderRadius: '2px',
                }}
                onClick={() => onTermClick(part)}
              >
                {part}
              </Text>
            )
          }
          return <span key={index}>{part}</span>
        })}
      </Text>
    )
  }

  return (
    <Paper withBorder h="100%">
      <Tabs
        value={selectedFileId?.toString() ?? ''}
        onChange={(value) => value && onFileSelect(parseInt(value, 10))}
        h="100%"
      >
        <Tabs.List>
          {files.map((file) => (
            <Tabs.Tab
              key={file.id}
              value={file.id.toString()}
              leftSection={<IconFile size={14} />}
            >
              {file.file_name}
            </Tabs.Tab>
          ))}
        </Tabs.List>

        <ScrollArea h="calc(100% - 42px)" p="md">
          {isLoading ? (
            <Center h={200}>
              <Loader />
            </Center>
          ) : content ? (
            renderHighlightedContent(content)
          ) : (
            <Text c="dimmed">Select a file to view its content</Text>
          )}
        </ScrollArea>
      </Tabs>
    </Paper>
  )
}
