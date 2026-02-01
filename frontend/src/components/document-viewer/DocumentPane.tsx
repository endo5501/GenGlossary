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
  const renderHighlightedContent = (text: string) => {
    if (terms.length === 0) {
      return <Text style={{ whiteSpace: 'pre-wrap' }}>{text}</Text>
    }

    // Escape special regex characters and sort by length (longest first)
    const escapedTerms = terms
      .map((t) => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
      .sort((a, b) => b.length - a.length)

    const pattern = new RegExp(`(${escapedTerms.join('|')})`, 'g')
    const parts = text.split(pattern)

    return (
      <Text style={{ whiteSpace: 'pre-wrap' }}>
        {parts.map((part, index) => {
          const isTermMatch = terms.some(
            (t) => t.toLowerCase() === part.toLowerCase()
          )
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
