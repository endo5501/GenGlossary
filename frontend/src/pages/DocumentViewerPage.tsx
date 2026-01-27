import { Box, Text, Title, Card, Stack, Tabs } from '@mantine/core'
import { IconFile, IconTags } from '@tabler/icons-react'

interface DocumentViewerPageProps {
  projectId: number
  fileId?: number
}

export function DocumentViewerPage({ projectId, fileId }: DocumentViewerPageProps) {
  return (
    <Box p="md">
      <Title order={2} mb="lg">Document Viewer</Title>

      <Tabs defaultValue="document">
        <Tabs.List>
          <Tabs.Tab value="document" leftSection={<IconFile size={16} />}>
            Document
          </Tabs.Tab>
          <Tabs.Tab value="terms" leftSection={<IconTags size={16} />}>
            Terms
          </Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="document" pt="lg">
          <Card withBorder p="xl">
            <Stack align="center" gap="md">
              <Text c="dimmed">
                {fileId
                  ? `Document content will be displayed here for file ID: ${fileId}`
                  : 'Select a file to view its content'}
              </Text>
              <Text size="sm" c="dimmed">
                Project ID: {projectId}
              </Text>
            </Stack>
          </Card>
        </Tabs.Panel>

        <Tabs.Panel value="terms" pt="lg">
          <Card withBorder p="xl">
            <Stack align="center" gap="md">
              <Text c="dimmed">
                Term cards will be displayed here
              </Text>
            </Stack>
          </Card>
        </Tabs.Panel>
      </Tabs>
    </Box>
  )
}
