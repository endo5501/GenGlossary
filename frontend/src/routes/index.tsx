import {
  createRootRoute,
  createRoute,
  createRouter,
} from '@tanstack/react-router'
import { AppShell } from '../components/layout'
import { PagePlaceholder } from '../components/common/PagePlaceholder'
import {
  HomePage,
  FilesPage,
  DocumentViewerPage,
  SettingsPage,
  TermsPage,
  ProvisionalPage,
  IssuesPage,
  RefinedPage,
} from '../pages'

// Root route with AppShell layout
const rootRoute = createRootRoute({
  component: AppShell,
})

// Home route (project list)
const homeRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: HomePage,
})

// Project-scoped routes
const projectFilesRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/projects/$projectId/files',
  component: () => {
    const { projectId } = projectFilesRoute.useParams()
    return <FilesPage projectId={Number(projectId)} />
  },
})

const projectDocumentViewerRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/projects/$projectId/document-viewer',
  component: () => {
    const { projectId } = projectDocumentViewerRoute.useParams()
    return <DocumentViewerPage projectId={Number(projectId)} />
  },
})

const projectSettingsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/projects/$projectId/settings',
  component: () => {
    const { projectId } = projectSettingsRoute.useParams()
    return <SettingsPage projectId={Number(projectId)} />
  },
})

const projectTermsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/projects/$projectId/terms',
  component: () => {
    const { projectId } = projectTermsRoute.useParams()
    return <TermsPage projectId={Number(projectId)} />
  },
})

const projectProvisionalRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/projects/$projectId/provisional',
  component: () => {
    const { projectId } = projectProvisionalRoute.useParams()
    return <ProvisionalPage projectId={Number(projectId)} />
  },
})

const projectIssuesRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/projects/$projectId/issues',
  component: () => {
    const { projectId } = projectIssuesRoute.useParams()
    return <IssuesPage projectId={Number(projectId)} />
  },
})

const projectRefinedRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/projects/$projectId/refined',
  component: () => {
    const { projectId } = projectRefinedRoute.useParams()
    return <RefinedPage projectId={Number(projectId)} />
  },
})

// Legacy placeholder routes for other pages (when no project is selected)
const placeholderConfigs = [
  { path: '/files', title: 'Files' },
  { path: '/terms', title: 'Terms' },
  { path: '/provisional', title: 'Provisional Glossary' },
  { path: '/issues', title: 'Issues' },
  { path: '/refined', title: 'Refined Glossary' },
  { path: '/document-viewer', title: 'Document Viewer' },
  { path: '/settings', title: 'Settings' },
] as const

const placeholderRoutes = placeholderConfigs.map(({ path, title }) =>
  createRoute({
    getParentRoute: () => rootRoute,
    path,
    component: () => <PagePlaceholder title={title} />,
  })
)

// Create route tree
export const routeTree = rootRoute.addChildren([
  homeRoute,
  projectFilesRoute,
  projectDocumentViewerRoute,
  projectSettingsRoute,
  projectTermsRoute,
  projectProvisionalRoute,
  projectIssuesRoute,
  projectRefinedRoute,
  ...placeholderRoutes,
])

// Create router instance
export const router = createRouter({ routeTree })

// Declare router types
declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}
