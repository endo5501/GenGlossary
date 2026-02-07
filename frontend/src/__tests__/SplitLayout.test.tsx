import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MantineProvider } from '@mantine/core'
import { SplitLayout } from '../components/common/SplitLayout'

const renderSplitLayout = (detail: React.ReactNode | null) => {
  return render(
    <MantineProvider>
      <SplitLayout
        list={<div data-testid="list-content">List</div>}
        detail={detail}
      />
    </MantineProvider>
  )
}

describe('SplitLayout', () => {
  it('should render list content', () => {
    renderSplitLayout(null)
    expect(screen.getByTestId('list-content')).toBeInTheDocument()
  })

  it('should not render detail panel when detail is null', () => {
    const { container } = renderSplitLayout(null)
    expect(container.querySelector('.split-layout-detail')).not.toBeInTheDocument()
  })

  it('should render detail panel when detail is provided', () => {
    renderSplitLayout(<div data-testid="detail-content">Detail</div>)
    expect(screen.getByTestId('detail-content')).toBeInTheDocument()
  })

  it('should render both list and detail when detail is provided', () => {
    renderSplitLayout(<div data-testid="detail-content">Detail</div>)
    expect(screen.getByTestId('list-content')).toBeInTheDocument()
    expect(screen.getByTestId('detail-content')).toBeInTheDocument()
  })

  it('should use split-layout class on container', () => {
    const { container } = renderSplitLayout(null)
    expect(container.querySelector('.split-layout')).toBeInTheDocument()
  })

  it('should use split-layout-list class on list panel', () => {
    const { container } = renderSplitLayout(null)
    expect(container.querySelector('.split-layout-list')).toBeInTheDocument()
  })

  it('should use split-layout-detail class on detail panel', () => {
    const { container } = renderSplitLayout(
      <div data-testid="detail-content">Detail</div>
    )
    expect(container.querySelector('.split-layout-detail')).toBeInTheDocument()
  })
})
