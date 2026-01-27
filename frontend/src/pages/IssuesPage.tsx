import {
  Box,
  Button,
  Group,
  Badge,
  Text,
  Paper,
  Stack,
  Select,
} from '@mantine/core'
import { IconRefresh } from '@tabler/icons-react'
import { useState } from 'react'
import { useIssues, useReviewIssues, useCurrentRun } from '../api/hooks'
import type { IssueResponse } from '../api/types'
import { PageContainer } from '../components/common/PageContainer'
import { severityColors, issueTypeColors } from '../utils/colors'

interface IssuesPageProps {
  projectId: number
}

const issueTypeOptions = [
  { value: '', label: 'All Types' },
  { value: 'ambiguous', label: 'Ambiguous' },
  { value: 'inconsistent', label: 'Inconsistent' },
  { value: 'missing', label: 'Missing' },
]

export function IssuesPage({ projectId }: IssuesPageProps) {
  const [issueTypeFilter, setIssueTypeFilter] = useState<string>('')
  const { data: issues, isLoading } = useIssues(
    projectId,
    issueTypeFilter || undefined
  )
  const { data: currentRun } = useCurrentRun(projectId)
  const [selectedIssue, setSelectedIssue] = useState<IssueResponse | null>(null)

  const reviewIssues = useReviewIssues(projectId)

  const isRunning = currentRun?.status === 'running'

  const actionBar = (
    <>
      <Button
        leftSection={<IconRefresh size={16} />}
        onClick={() => reviewIssues.mutate()}
        disabled={isRunning}
        aria-label="Review issues"
      >
        Review
      </Button>
      <Box data-testid="issue-type-filter">
        <Select
          value={issueTypeFilter}
          onChange={(val) => setIssueTypeFilter(val ?? '')}
          data={issueTypeOptions}
          placeholder="Filter by type"
          clearable
          w={150}
        />
      </Box>
    </>
  )

  return (
    <PageContainer
      isLoading={isLoading}
      isEmpty={!issues || issues.length === 0}
      emptyMessage="No issues found. Great job!"
      actionBar={actionBar}
      loadingTestId="issues-loading"
      emptyTestId="issues-empty"
    >
      <Box style={{ flex: 1 }}>
        <Stack gap="sm">
          {issues?.map((issue) => (
            <Paper
              key={issue.id}
              withBorder
              p="sm"
              onClick={() => setSelectedIssue(issue)}
              style={{ cursor: 'pointer' }}
              bg={
                selectedIssue?.id === issue.id
                  ? 'var(--mantine-color-blue-light)'
                  : undefined
              }
            >
              <Group justify="space-between" mb="xs">
                <Group gap="xs">
                  <Badge
                    color={issueTypeColors[issue.issue_type] ?? 'gray'}
                    variant="light"
                  >
                    {issue.issue_type}
                  </Badge>
                  <Badge color={severityColors[issue.severity]} variant="outline">
                    {issue.severity}
                  </Badge>
                </Group>
              </Group>
              <Text size="sm">{issue.description}</Text>
            </Paper>
          ))}
        </Stack>
      </Box>

      {selectedIssue && (
        <Paper data-testid="issue-detail-panel" withBorder p="md">
          <Group mb="md">
            <Badge
              color={issueTypeColors[selectedIssue.issue_type] ?? 'gray'}
              size="lg"
            >
              {selectedIssue.issue_type}
            </Badge>
            <Badge
              color={severityColors[selectedIssue.severity]}
              size="lg"
              variant="outline"
            >
              {selectedIssue.severity}
            </Badge>
          </Group>

          <Text fw={500} mb="xs">
            Description
          </Text>
          <Text>{selectedIssue.description}</Text>

          {selectedIssue.term_id && (
            <Box mt="md">
              <Text size="sm" c="dimmed">
                Related Term ID: {selectedIssue.term_id}
              </Text>
            </Box>
          )}
        </Paper>
      )}
    </PageContainer>
  )
}
