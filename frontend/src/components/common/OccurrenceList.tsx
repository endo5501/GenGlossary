import { Text, Paper, Stack } from '@mantine/core'

interface Occurrence {
  document_path: string
  line_number: number
  context: string
}

interface OccurrenceListProps {
  occurrences: Occurrence[]
}

export function OccurrenceList({ occurrences }: OccurrenceListProps) {
  return (
    <Stack gap="xs">
      {occurrences.map((occ) => (
        <Paper key={`${occ.document_path}:${occ.line_number}`} withBorder p="xs">
          <Text size="sm" c="dimmed">
            {occ.document_path}:{occ.line_number}
          </Text>
          <Text size="sm">{occ.context}</Text>
        </Paper>
      ))}
    </Stack>
  )
}
