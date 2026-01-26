import { Box, Text, Title } from '@mantine/core'

interface PagePlaceholderProps {
  title: string
}

export function PagePlaceholder({ title }: PagePlaceholderProps) {
  return (
    <Box p="md">
      <Title order={2} mb="md">{title}</Title>
      <Text c="dimmed">This page will be implemented in a future ticket.</Text>
    </Box>
  )
}
