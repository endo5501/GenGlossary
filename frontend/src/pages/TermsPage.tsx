import {
  Box,
  Button,
  Center,
  Group,
  Loader,
  Table,
  Badge,
  Text,
  Paper,
  Stack,
  TextInput,
  Textarea,
  Modal,
  ActionIcon,
  Tabs,
  Tooltip,
} from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import { IconPlus, IconRefresh, IconTrash, IconBan, IconList, IconPencil, IconCheck, IconX, IconStar } from '@tabler/icons-react'
import { useState, useEffect, useRef, useCallback } from 'react'
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
  useSynonymGroups,
  useCreateSynonymGroup,
  useDeleteSynonymGroup,
  useAddSynonymMember,
  useRemoveSynonymMember,
  useUpdateSynonymGroup,
} from '../api/hooks'
import { PageContainer } from '../components/common/PageContainer'
import { SplitLayout } from '../components/common/SplitLayout'
import { AddTermModal } from '../components/common/AddTermModal'
import { TermListTable } from '../components/common/TermListTable'
import { SynonymGroupPanel } from '../components/common/SynonymGroupPanel'

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
  const [activeTab, setActiveTab] = useState<string | null>('terms')
  const [editingCategoryValue, setEditingCategoryValue] = useState<string | null>(null)
  const isEditingCategory = editingCategoryValue !== null
  const [userNotesValue, setUserNotesValue] = useState('')
  const debounceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Cleanup debounce timer on unmount
  useEffect(() => {
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current)
      }
    }
  }, [])

  const createTerm = useCreateTerm(projectId)
  const updateTerm = useUpdateTerm(projectId)
  const deleteTerm = useDeleteTerm(projectId)
  const extractTerms = useExtractTerms(projectId)
  const createExcludedTerm = useCreateExcludedTerm(projectId)
  const deleteExcludedTerm = useDeleteExcludedTerm(projectId)
  const createRequiredTerm = useCreateRequiredTerm(projectId)
  const deleteRequiredTerm = useDeleteRequiredTerm(projectId)
  const { data: synonymGroups } = useSynonymGroups(projectId)
  const createSynonymGroup = useCreateSynonymGroup(projectId)
  const deleteSynonymGroup = useDeleteSynonymGroup(projectId)
  const addSynonymMember = useAddSynonymMember(projectId)
  const removeSynonymMember = useRemoveSynonymMember(projectId)
  const updateSynonymGroup = useUpdateSynonymGroup(projectId)

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

  const handleAddExcludedTerm = (termText: string) => {
    createExcludedTerm.mutate(
      { term_text: termText },
      { onSuccess: closeExcludedModal }
    )
  }

  const handleDeleteRequiredTerm = (termId: number) => {
    deleteRequiredTerm.mutate(termId)
  }

  const handleAddRequiredTerm = (termText: string) => {
    createRequiredTerm.mutate(
      { term_text: termText },
      { onSuccess: closeRequiredModal }
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
    const term = terms?.find((t) => t.id === termId)
    setUserNotesValue(term?.user_notes ?? '')
  }

  const handleUserNotesChange = useCallback((value: string) => {
    setUserNotesValue(value)

    // Debounce save (500ms)
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current)
    }
    debounceTimerRef.current = setTimeout(() => {
      if (selectedTerm) {
        updateTerm.mutate({
          termId: selectedTerm.id,
          data: { user_notes: value },
        })
      }
    }, 500)
  }, [selectedTerm, updateTerm])

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

  const tabActionBars: Record<string, React.ReactNode> = {
    terms: termsActionBar,
    excluded: excludedActionBar,
    required: requiredActionBar,
  }

  return (
    <>
      <PageContainer
        isLoading={isLoading}
        isEmpty={false}
        emptyMessage=""
        actionBar={tabActionBars[activeTab ?? 'terms']}
        loadingTestId="terms-loading"
      >
        <SplitLayout
          list={
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
                {!terms || terms.length === 0 ? (
                  <Center data-testid="terms-empty" style={{ flex: 1 }}>
                    <Text c="dimmed">No terms found. Extract terms from documents or add manually.</Text>
                  </Center>
                ) : (
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
                )}
              </Tabs.Panel>

              <Tabs.Panel value="excluded">
                {isLoadingExcluded ? (
                  <Center style={{ flex: 1 }}><Loader /></Center>
                ) : !excludedTerms || excludedTerms.length === 0 ? (
                  <Center data-testid="excluded-terms-empty" style={{ flex: 1 }}>
                    <Text c="dimmed">No excluded terms. Add terms to exclude them from extraction.</Text>
                  </Center>
                ) : (
                  <TermListTable
                    terms={excludedTerms}
                    onDelete={handleDeleteExcludedTerm}
                    isLoading={isLoadingExcluded}
                    isDeletePending={deleteExcludedTerm.isPending}
                    showSourceColumn={true}
                    deleteTooltip="除外リストから削除"
                    deleteAriaLabel="Remove from excluded"
                  />
                )}
              </Tabs.Panel>

              <Tabs.Panel value="required">
                {isLoadingRequired ? (
                  <Center style={{ flex: 1 }}><Loader /></Center>
                ) : !requiredTerms || requiredTerms.length === 0 ? (
                  <Center data-testid="required-terms-empty" style={{ flex: 1 }}>
                    <Text c="dimmed">No required terms. Add terms to always include them in extraction.</Text>
                  </Center>
                ) : (
                  <TermListTable
                    terms={requiredTerms}
                    onDelete={handleDeleteRequiredTerm}
                    isLoading={isLoadingRequired}
                    isDeletePending={deleteRequiredTerm.isPending}
                    showSourceColumn={false}
                    deleteTooltip="必須リストから削除"
                    deleteAriaLabel="Remove from required"
                  />
                )}
              </Tabs.Panel>
            </Tabs>
          }
          detail={selectedTerm && activeTab === 'terms' ? (
            <Paper data-testid="term-detail-panel" withBorder p="md">
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

              <Textarea
                label="補足情報"
                placeholder="この用語に関する補足情報を入力（用語集生成時にLLMへ提供されます）"
                value={userNotesValue}
                onChange={(e) => handleUserNotesChange(e.target.value)}
                minRows={3}
                autosize
                mb="md"
              />

              <SynonymGroupPanel
                termText={selectedTerm.term_text}
                synonymGroups={synonymGroups}
                terms={terms}
                projectId={projectId}
                onCreateGroup={(primaryText, memberTexts) =>
                  createSynonymGroup.mutate({ primary_term_text: primaryText, member_texts: memberTexts })
                }
                onDeleteGroup={(groupId) => deleteSynonymGroup.mutate(groupId)}
                onAddMember={(groupId, termText) =>
                  addSynonymMember.mutate({ groupId, data: { term_text: termText } })
                }
                onRemoveMember={(groupId, memberId) =>
                  removeSynonymMember.mutate({ groupId, memberId })
                }
                onUpdatePrimary={(groupId, newPrimaryText) =>
                  updateSynonymGroup.mutate({ groupId, data: { primary_term_text: newPrimaryText } })
                }
                isLoading={createSynonymGroup.isPending || addSynonymMember.isPending}
              />
            </Paper>
          ) : null}
        />
      </PageContainer>

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

      <AddTermModal
        opened={excludedModalOpened}
        onClose={closeExcludedModal}
        onSubmit={handleAddExcludedTerm}
        title="除外用語を追加"
        placeholder="除外する用語を入力"
        isLoading={createExcludedTerm.isPending}
      />

      <AddTermModal
        opened={requiredModalOpened}
        onClose={closeRequiredModal}
        onSubmit={handleAddRequiredTerm}
        title="必須用語を追加"
        placeholder="必須にする用語を入力"
        isLoading={createRequiredTerm.isPending}
      />
    </>
  )
}
