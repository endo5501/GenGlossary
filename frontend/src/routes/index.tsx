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

// Index route (redirects to /files)
const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: () => <PagePlaceholder title="Home" />,
})

// Files route
const filesRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/files',
  component: () => <PagePlaceholder title="Files" />,
})

// Terms route
const termsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/terms',
  component: () => <PagePlaceholder title="Terms" />,
})

// Provisional glossary route
const provisionalRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/provisional',
  component: () => <PagePlaceholder title="Provisional Glossary" />,
})

// Issues route
const issuesRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/issues',
  component: () => <PagePlaceholder title="Issues" />,
})

// Refined glossary route
const refinedRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/refined',
  component: () => <PagePlaceholder title="Refined Glossary" />,
})

// Document viewer route
const documentViewerRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/document-viewer',
  component: () => <PagePlaceholder title="Document Viewer" />,
})

// Settings route
const settingsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/settings',
  component: () => <PagePlaceholder title="Settings" />,
})

// Create route tree
export const routeTree = rootRoute.addChildren([
  indexRoute,
  filesRoute,
  termsRoute,
  provisionalRoute,
  issuesRoute,
  refinedRoute,
  documentViewerRoute,
  settingsRoute,
])

// Create router instance
export const router = createRouter({ routeTree })

// Declare router types
declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}
