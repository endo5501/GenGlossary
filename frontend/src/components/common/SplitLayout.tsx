import { Box } from '@mantine/core'
import type { ReactNode } from 'react'

interface SplitLayoutProps {
  list: ReactNode
  detail: ReactNode | null
}

export function SplitLayout({ list, detail }: SplitLayoutProps) {
  return (
    <Box className="split-layout">
      <Box className="split-layout-list">
        {list}
      </Box>
      {detail && (
        <Box className="split-layout-detail">
          {detail}
        </Box>
      )}
    </Box>
  )
}
