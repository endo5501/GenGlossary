import { useState } from 'react'
import {
  Box,
  Button,
  Card,
  Group,
  Skeleton,
  Stack,
  Table,
  Text,
  Title,
  Badge,
} from '@mantine/core'
import { IconPlus, IconTrash, IconCopy, IconFolderOpen } from '@tabler/icons-react'
import { useProjects } from '../api/hooks'
import type { ProjectResponse, ProjectStatus } from '../api/types'
import { CreateProjectDialog } from '../components/dialogs/CreateProjectDialog'
import { CloneProjectDialog } from '../components/dialogs/CloneProjectDialog'
import { DeleteProjectDialog } from '../components/dialogs/DeleteProjectDialog'

const statusColors: Record<ProjectStatus, string> = {
  created: 'blue',
  running: 'yellow',
  completed: 'green',
  error: 'red',
}

function ProjectSummaryCard({
  project,
  onDelete,
  onClone,
  onOpen,
}: {
  project: ProjectResponse
  onDelete: () => void
  onClone: () => void
  onOpen: () => void
}) {
  return (
    <Card data-testid="project-summary-card" withBorder p="lg">
      <Stack gap="md">
        <Group justify="space-between">
          <Title order={3}>{project.name}</Title>
          <Badge color={statusColors[project.status]}>{project.status}</Badge>
        </Group>

        <Stack gap="xs">
          <Text size="sm">
            <strong>Document Root:</strong> {project.doc_root}
          </Text>
          <Text size="sm">
            <strong>LLM Provider:</strong> {project.llm_provider}
          </Text>
          <Text size="sm">
            <strong>LLM Model:</strong> {project.llm_model || '(not set)'}
          </Text>
          <Text size="sm">
            <strong>Last Run:</strong>{' '}
            {project.last_run_at
              ? new Date(project.last_run_at).toLocaleString()
              : 'Never'}
          </Text>
        </Stack>

        <Group gap="sm">
          <Button
            leftSection={<IconFolderOpen size={16} />}
            onClick={onOpen}
          >
            Open
          </Button>
          <Button
            variant="outline"
            leftSection={<IconCopy size={16} />}
            onClick={onClone}
          >
            Clone
          </Button>
          <Button
            variant="outline"
            color="red"
            leftSection={<IconTrash size={16} />}
            onClick={onDelete}
          >
            Delete
          </Button>
        </Group>
      </Stack>
    </Card>
  )
}

export function HomePage() {
  const { data: projects, isLoading, error } = useProjects()
  const [selectedProject, setSelectedProject] = useState<ProjectResponse | null>(null)
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [cloneDialogOpen, setCloneDialogOpen] = useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)

  if (isLoading) {
    return (
      <Box p="md" data-testid="projects-loading">
        <Skeleton height={40} mb="md" />
        <Skeleton height={100} mb="sm" />
        <Skeleton height={100} mb="sm" />
        <Skeleton height={100} />
      </Box>
    )
  }

  if (error) {
    return (
      <Box p="md" data-testid="projects-error">
        <Text c="red">Error loading projects: {error.message}</Text>
      </Box>
    )
  }

  const isEmpty = !projects || projects.length === 0

  return (
    <Box p="md">
      <Group justify="space-between" mb="lg">
        <Title order={2}>Projects</Title>
        <Button
          leftSection={<IconPlus size={16} />}
          onClick={() => setCreateDialogOpen(true)}
        >
          Create
        </Button>
      </Group>

      {isEmpty ? (
        <Card withBorder p="xl" data-testid="projects-empty">
          <Stack align="center" gap="md">
            <Text size="lg" c="dimmed">
              No projects yet
            </Text>
            <Text c="dimmed">
              Create your first project to get started.
            </Text>
            <Button
              leftSection={<IconPlus size={16} />}
              onClick={() => setCreateDialogOpen(true)}
            >
              Create Project
            </Button>
          </Stack>
        </Card>
      ) : (
        <Group align="flex-start" gap="lg">
          {/* Project List */}
          <Card withBorder style={{ flex: 1 }}>
            <Table highlightOnHover>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Name</Table.Th>
                  <Table.Th>Status</Table.Th>
                  <Table.Th>Last Run</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {projects.map((project) => (
                  <Table.Tr
                    key={project.id}
                    onClick={() => setSelectedProject(project)}
                    style={{
                      cursor: 'pointer',
                      backgroundColor:
                        selectedProject?.id === project.id
                          ? 'var(--mantine-color-blue-light)'
                          : undefined,
                    }}
                  >
                    <Table.Td>{project.name}</Table.Td>
                    <Table.Td>
                      <Badge color={statusColors[project.status]} size="sm">
                        {project.status}
                      </Badge>
                    </Table.Td>
                    <Table.Td>
                      {project.last_run_at
                        ? new Date(project.last_run_at).toLocaleDateString()
                        : '-'}
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </Card>

          {/* Summary Card */}
          {selectedProject && (
            <Box style={{ width: 350 }}>
              <ProjectSummaryCard
                project={selectedProject}
                onDelete={() => setDeleteDialogOpen(true)}
                onClone={() => setCloneDialogOpen(true)}
                onOpen={() => {
                  // Navigate to files page
                  window.location.href = `/projects/${selectedProject.id}/files`
                }}
              />
            </Box>
          )}
        </Group>
      )}

      {/* Dialogs */}
      <CreateProjectDialog
        opened={createDialogOpen}
        onClose={() => setCreateDialogOpen(false)}
      />

      {selectedProject && (
        <>
          <CloneProjectDialog
            opened={cloneDialogOpen}
            onClose={() => setCloneDialogOpen(false)}
            project={selectedProject}
          />
          <DeleteProjectDialog
            opened={deleteDialogOpen}
            onClose={() => setDeleteDialogOpen(false)}
            project={selectedProject}
            onDeleted={() => setSelectedProject(null)}
          />
        </>
      )}
    </Box>
  )
}
