import {
  Box,
  Button,
  Group,
  Table,
  Badge,
  Text,
  Paper,
  Stack,
  TextInput,
  Modal,
  ActionIcon,
  Tabs,
  Tooltip,
  LoadingOverlay,
} from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import { IconPlus, IconRefresh, IconTrash, IconBan, IconList, IconPencil, IconCheck, IconX, IconStar } from '@tabler/icons-react'
import { useState } from 'react'
import {
  useTerms,
  useCreateTerm,
  useUpdateTerm,
  useDeleteTerm,
  useExtractTerms,
  useCurrentRun,
  useExcludedTerms,
  useCreateExcludedTerm,
  useDeleteExcludedTerm,
  useRequiredTerms,
  useCreateRequiredTerm,
  useDeleteRequiredTerm,
} from '../api/hooks'
import { PageContainer } from '../components/common/PageContainer'

interface TermsPageProps {
  projectId: number
}

export function TermsPage({ projectId }: TermsPageProps) {
  const { data: terms, isLoading } = useTerms(projectId)
  const { data: excludedTerms, isLoading: isLoadingExcluded } = useExcludedTerms(projectId)
  const { data: requiredTerms, isLoading: isLoadingRequired } = useRequiredTerms(projectId)
  const { data: currentRun } = useCurrentRun(projectId)
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const selectedTerm = terms?.find((t) => t.id === selectedId) ?? null
  const [opened, { open, close }] = useDisclosure(false)
  const [excludedModalOpened, { open: openExcludedModal, close: closeExcludedModal }] =
    useDisclosure(false)
  const [requiredModalOpened, { open: openRequiredModal, close: closeRequiredModal }] =
    useDisclosure(false)
  const [newTermText, setNewTermText] = useState('')
  const [newTermCategory, setNewTermCategory] = useState('')
  const [newExcludedTermText, setNewExcludedTermText] = useState('')
  const [newRequiredTermText, setNewRequiredTermText] = useState('')
  const [activeTab, setActiveTab] = useState<string | null>('terms')
  const [editingCategoryValue, setEditingCategoryValue] = useState<string | null>(null)
  const isEditingCategory = editingCategoryValue !== null

  const createTerm = useCreateTerm(projectId)
  const updateTerm = useUpdateTerm(projectId)
  const deleteTerm = useDeleteTerm(projectId)
  const extractTerms = useExtractTerms(projectId)
  const createExcludedTerm = useCreateExcludedTerm(projectId)
  const deleteExcludedTerm = useDeleteExcludedTerm(projectId)
  const createRequiredTerm = useCreateRequiredTerm(projectId)
  const deleteRequiredTerm = useDeleteRequiredTerm(projectId)

  const isRunning = currentRun?.status === 'running'

  const handleAddTerm = () => {
    if (!newTermText.trim()) return
    createTerm.mutate(
      { term_text: newTermText.trim(), category: newTermCategory.trim() || undefined },
      {
        onSuccess: () => {
          setNewTermText('')
          setNewTermCategory('')
          close()
        },
      }
    )
  }

  const handleDeleteTerm = (termId: number) => {
    deleteTerm.mutate(termId, {
      onSuccess: () => {
        if (selectedId === termId) {
          setSelectedId(null)
        }
      },
    })
  }

  const handleAddToExcluded = (termText: string) => {
    createExcludedTerm.mutate({ term_text: termText })
  }

  const handleDeleteExcludedTerm = (termId: number) => {
    deleteExcludedTerm.mutate(termId)
  }

  const handleAddExcludedTerm = () => {
    if (!newExcludedTermText.trim()) return
    createExcludedTerm.mutate(
      { term_text: newExcludedTermText.trim() },
      {
        onSuccess: () => {
          setNewExcludedTermText('')
          closeExcludedModal()
        },
      }
    )
  }

  const handleDeleteRequiredTerm = (termId: number) => {
    deleteRequiredTerm.mutate(termId)
  }

  const handleAddRequiredTerm = () => {
    if (!newRequiredTermText.trim()) return
    createRequiredTerm.mutate(
      { term_text: newRequiredTermText.trim() },
      {
        onSuccess: () => {
          setNewRequiredTermText('')
          closeRequiredModal()
        },
      }
    )
  }

  const handleStartEditCategory = () => {
    setEditingCategoryValue(selectedTerm?.category ?? '')
  }

  const resetCategoryEdit = () => {
    setEditingCategoryValue(null)
  }

  const handleCancelEditCategory = () => {
    resetCategoryEdit()
  }

  const handleSelectTerm = (termId: number) => {
    if (termId !== selectedId) {
      resetCategoryEdit()
    }
    setSelectedId(termId)
  }

  const handleSaveCategory = () => {
    if (!selectedTerm || updateTerm.isPending || editingCategoryValue === null) return
    const trimmedValue = editingCategoryValue.trim()
    updateTerm.mutate(
      {
        termId: selectedTerm.id,
        data: { category: trimmedValue || undefined },
      },
      {
        onSuccess: resetCategoryEdit,
      }
    )
  }

  const termsActionBar = (
    <>
      <Button
        leftSection={<IconRefresh size={16} />}
        onClick={() => extractTerms.mutate()}
        disabled={isRunning}
        aria-label="Extract terms"
      >
        Extract
      </Button>
      <Button
        leftSection={<IconPlus size={16} />}
        onClick={open}
        disabled={isRunning}
        aria-label="Add term"
      >
        Add
      </Button>
    </>
  )

  const excludedActionBar = (
    <Button
      leftSection={<IconPlus size={16} />}
      onClick={openExcludedModal}
      aria-label="Add excluded term"
    >
      Add
    </Button>
  )

  const requiredActionBar = (
    <Button
      leftSection={<IconPlus size={16} />}
      onClick={openRequiredModal}
      aria-label="Add required term"
    >
      Add
    </Button>
  )

  const actionBar =
    activeTab === 'terms'
      ? termsActionBar
      : activeTab === 'excluded'
        ? excludedActionBar
        : requiredActionBar

  const isTermsEmpty = !terms || terms.length === 0
  const isExcludedEmpty = !excludedTerms || excludedTerms.length === 0
  const isRequiredEmpty = !requiredTerms || requiredTerms.length === 0
  const isEmpty =
    activeTab === 'terms'
      ? isTermsEmpty
      : activeTab === 'excluded'
        ? isExcludedEmpty
        : isRequiredEmpty
  const emptyMessage =
    activeTab === 'terms'
      ? 'No terms found. Extract terms from documents or add manually.'
      : activeTab === 'excluded'
        ? 'No excluded terms. Add terms to exclude them from extraction.'
        : 'No required terms. Add terms to always include them in extraction.'

  return (
    <PageContainer
      isLoading={isLoading && activeTab === 'terms'}
      isEmpty={isEmpty}
      emptyMessage={emptyMessage}
      actionBar={actionBar}
      loadingTestId="terms-loading"
      emptyTestId={
        activeTab === 'terms'
          ? 'terms-empty'
          : activeTab === 'excluded'
            ? 'excluded-terms-empty'
            : 'required-terms-empty'
      }
    >
      <Tabs value={activeTab} onChange={setActiveTab}>
        <Tabs.List mb="md">
          <Tabs.Tab value="terms" leftSection={<IconList size={16} />}>
            用語一覧
          </Tabs.Tab>
          <Tabs.Tab value="excluded" leftSection={<IconBan size={16} />}>
            除外用語
          </Tabs.Tab>
          <Tabs.Tab value="required" leftSection={<IconStar size={16} />}>
            必須用語
          </Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="terms">
          <Box style={{ flex: 1 }}>
            <Table highlightOnHover>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Term</Table.Th>
                  <Table.Th>Category</Table.Th>
                  <Table.Th w={100}>Actions</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {terms?.map((term) => (
                  <Table.Tr
                    key={term.id}
                    onClick={() => handleSelectTerm(term.id)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault()
                        handleSelectTerm(term.id)
                      }
                    }}
                    tabIndex={0}
                    role="button"
                    aria-selected={selectedId === term.id}
                    style={{ cursor: 'pointer' }}
                    bg={selectedId === term.id ? 'var(--mantine-color-blue-light)' : undefined}
                  >
                    <Table.Td>{term.term_text}</Table.Td>
                    <Table.Td>
                      {term.category ? (
                        <Badge variant="light">{term.category}</Badge>
                      ) : (
                        <Text c="dimmed" size="sm">
                          -
                        </Text>
                      )}
                    </Table.Td>
                    <Table.Td>
                      <Group gap="xs">
                        <Tooltip label="除外に追加">
                          <ActionIcon
                            variant="subtle"
                            color="orange"
                            onClick={(e) => {
                              e.stopPropagation()
                              handleAddToExcluded(term.term_text)
                            }}
                            aria-label="Add to excluded"
                            loading={createExcludedTerm.isPending}
                          >
                            <IconBan size={16} />
                          </ActionIcon>
                        </Tooltip>
                        <Tooltip label="削除">
                          <ActionIcon
                            variant="subtle"
                            color="red"
                            onClick={(e) => {
                              e.stopPropagation()
                              handleDeleteTerm(term.id)
                            }}
                            aria-label="Delete term"
                          >
                            <IconTrash size={16} />
                          </ActionIcon>
                        </Tooltip>
                      </Group>
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </Box>

          {selectedTerm && (
            <Paper data-testid="term-detail-panel" withBorder p="md" mt="md">
              <Group justify="space-between" mb="md">
                <Text fw={600} size="lg">
                  {selectedTerm.term_text}
                </Text>
                <ActionIcon
                  variant="subtle"
                  color="red"
                  onClick={() => handleDeleteTerm(selectedTerm.id)}
                  aria-label="Delete term"
                >
                  <IconTrash size={16} />
                </ActionIcon>
              </Group>

              {isEditingCategory ? (
                <Group gap="xs" mb="md">
                  <TextInput
                    value={editingCategoryValue}
                    onChange={(e) => setEditingCategoryValue(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        handleSaveCategory()
                      } else if (e.key === 'Escape') {
                        handleCancelEditCategory()
                      }
                    }}
                    placeholder="カテゴリを入力"
                    aria-label="カテゴリ"
                    size="sm"
                    disabled={updateTerm.isPending}
                  />
                  <ActionIcon
                    variant="subtle"
                    color="green"
                    onClick={handleSaveCategory}
                    aria-label="Save"
                    loading={updateTerm.isPending}
                  >
                    <IconCheck size={16} />
                  </ActionIcon>
                  <ActionIcon
                    variant="subtle"
                    color="gray"
                    onClick={handleCancelEditCategory}
                    aria-label="Cancel"
                    disabled={updateTerm.isPending}
                  >
                    <IconX size={16} />
                  </ActionIcon>
                </Group>
              ) : (
                <Group gap="xs" mb="md">
                  {selectedTerm.category ? (
                    <Badge variant="light">{selectedTerm.category}</Badge>
                  ) : (
                    <Text c="dimmed" size="sm">カテゴリなし</Text>
                  )}
                  <Tooltip label="カテゴリを編集">
                    <ActionIcon
                      variant="subtle"
                      color="blue"
                      onClick={handleStartEditCategory}
                      aria-label="Edit category"
                    >
                      <IconPencil size={16} />
                    </ActionIcon>
                  </Tooltip>
                </Group>
              )}
            </Paper>
          )}
        </Tabs.Panel>

        <Tabs.Panel value="excluded">
          <Box style={{ flex: 1, position: 'relative' }}>
            <LoadingOverlay visible={isLoadingExcluded} />
            <Table highlightOnHover>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Term</Table.Th>
                  <Table.Th>Source</Table.Th>
                  <Table.Th>Created At</Table.Th>
                  <Table.Th w={80}>Actions</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {excludedTerms?.map((term) => (
                  <Table.Tr key={term.id}>
                    <Table.Td>{term.term_text}</Table.Td>
                    <Table.Td>
                      <Badge variant="light" color={term.source === 'auto' ? 'blue' : 'green'}>
                        {term.source === 'auto' ? '自動' : '手動'}
                      </Badge>
                    </Table.Td>
                    <Table.Td>
                      <Text size="sm" c="dimmed">
                        {new Date(term.created_at).toLocaleDateString('ja-JP')}
                      </Text>
                    </Table.Td>
                    <Table.Td>
                      <Tooltip label="除外リストから削除">
                        <ActionIcon
                          variant="subtle"
                          color="red"
                          onClick={() => handleDeleteExcludedTerm(term.id)}
                          aria-label="Remove from excluded"
                          loading={deleteExcludedTerm.isPending}
                        >
                          <IconTrash size={16} />
                        </ActionIcon>
                      </Tooltip>
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </Box>
        </Tabs.Panel>

        <Tabs.Panel value="required">
          <Box style={{ flex: 1, position: 'relative' }}>
            <LoadingOverlay visible={isLoadingRequired} />
            <Table highlightOnHover>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Term</Table.Th>
                  <Table.Th>Created At</Table.Th>
                  <Table.Th w={80}>Actions</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {requiredTerms?.map((term) => (
                  <Table.Tr key={term.id}>
                    <Table.Td>{term.term_text}</Table.Td>
                    <Table.Td>
                      <Text size="sm" c="dimmed">
                        {new Date(term.created_at).toLocaleDateString('ja-JP')}
                      </Text>
                    </Table.Td>
                    <Table.Td>
                      <Tooltip label="必須リストから削除">
                        <ActionIcon
                          variant="subtle"
                          color="red"
                          onClick={() => handleDeleteRequiredTerm(term.id)}
                          aria-label="Remove from required"
                          loading={deleteRequiredTerm.isPending}
                        >
                          <IconTrash size={16} />
                        </ActionIcon>
                      </Tooltip>
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </Box>
        </Tabs.Panel>
      </Tabs>

      <Modal opened={opened} onClose={close} title="Add Term">
        <Stack>
          <TextInput
            label="Term"
            placeholder="Enter term text"
            value={newTermText}
            onChange={(e) => setNewTermText(e.target.value)}
            required
          />
          <TextInput
            label="Category"
            placeholder="Enter category (optional)"
            value={newTermCategory}
            onChange={(e) => setNewTermCategory(e.target.value)}
          />
          <Group justify="flex-end">
            <Button variant="subtle" onClick={close}>
              Cancel
            </Button>
            <Button onClick={handleAddTerm} loading={createTerm.isPending}>
              Add
            </Button>
          </Group>
        </Stack>
      </Modal>

      <Modal opened={excludedModalOpened} onClose={closeExcludedModal} title="除外用語を追加">
        <Stack>
          <TextInput
            label="用語"
            placeholder="除外する用語を入力"
            value={newExcludedTermText}
            onChange={(e) => setNewExcludedTermText(e.target.value)}
            required
          />
          <Group justify="flex-end">
            <Button variant="subtle" onClick={closeExcludedModal}>
              キャンセル
            </Button>
            <Button onClick={handleAddExcludedTerm} loading={createExcludedTerm.isPending}>
              追加
            </Button>
          </Group>
        </Stack>
      </Modal>

      <Modal opened={requiredModalOpened} onClose={closeRequiredModal} title="必須用語を追加">
        <Stack>
          <TextInput
            label="用語"
            placeholder="必須にする用語を入力"
            value={newRequiredTermText}
            onChange={(e) => setNewRequiredTermText(e.target.value)}
            required
          />
          <Group justify="flex-end">
            <Button variant="subtle" onClick={closeRequiredModal}>
              キャンセル
            </Button>
            <Button onClick={handleAddRequiredTerm} loading={createRequiredTerm.isPending}>
              追加
            </Button>
          </Group>
        </Stack>
      </Modal>
    </PageContainer>
  )
}
