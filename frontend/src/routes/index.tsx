import {
  createRootRoute,
  createRoute,
  createRouter,
} from '@tanstack/react-router'
import { AppShell } from '../components/layout'
import { PagePlaceholder } from '../components/common/PagePlaceholder'

// Root route with AppShell layout
const rootRoute = createRootRoute({
  component: AppShell,
})

// Route configuration data
const routeConfigs = [
  { path: '/', title: 'Home' },
  { path: '/files', title: 'Files' },
  { path: '/terms', title: 'Terms' },
  { path: '/provisional', title: 'Provisional Glossary' },
  { path: '/issues', title: 'Issues' },
  { path: '/refined', title: 'Refined Glossary' },
  { path: '/document-viewer', title: 'Document Viewer' },
  { path: '/settings', title: 'Settings' },
] as const

// Generate routes from configuration
const routes = routeConfigs.map(({ path, title }) =>
  createRoute({
    getParentRoute: () => rootRoute,
    path,
    component: () => <PagePlaceholder title={title} />,
  })
)

// Create route tree
export const routeTree = rootRoute.addChildren(routes)

// Create router instance
export const router = createRouter({ routeTree })

// Declare router types
declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}
