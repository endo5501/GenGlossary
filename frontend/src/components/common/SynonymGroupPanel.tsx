import {
  Badge,
  Button,
  Group,
  Stack,
  Text,
  ActionIcon,
  Tooltip,
  Autocomplete,
} from '@mantine/core'
import { IconPlus, IconTrash, IconStar, IconStarFilled } from '@tabler/icons-react'
import { useState } from 'react'
import type { SynonymGroupResponse, TermResponse } from '../../api/types'

interface SynonymGroupPanelProps {
  termText: string
  synonymGroups: SynonymGroupResponse[] | undefined
  terms: TermResponse[] | undefined
  projectId: number
  onCreateGroup: (primaryTermText: string, memberTexts: string[]) => void
  onDeleteGroup: (groupId: number) => void
  onAddMember: (groupId: number, termText: string) => void
  onRemoveMember: (groupId: number, memberId: number) => void
  onUpdatePrimary: (groupId: number, newPrimaryText: string) => void
  isLoading: boolean
}

export function SynonymGroupPanel({
  termText,
  synonymGroups,
  terms,
  onCreateGroup,
  onDeleteGroup,
  onAddMember,
  onRemoveMember,
  onUpdatePrimary,
  isLoading,
}: SynonymGroupPanelProps) {
  const [addTermText, setAddTermText] = useState('')

  // Find the group this term belongs to
  const currentGroup = synonymGroups?.find((g) =>
    g.members.some((m) => m.term_text === termText)
  )

  // Get available terms for autocomplete (not already in any group)
  const groupedTermTexts = new Set(
    synonymGroups?.flatMap((g) => g.members.map((m) => m.term_text)) ?? []
  )
  const availableTerms =
    terms
      ?.filter((t) => !groupedTermTexts.has(t.term_text) && t.term_text !== termText)
      .map((t) => t.term_text) ?? []

  const handleCreateGroup = () => {
    onCreateGroup(termText, [termText])
  }

  const handleAddMember = () => {
    if (!currentGroup || !addTermText.trim()) return
    onAddMember(currentGroup.id, addTermText.trim())
    setAddTermText('')
  }

  if (!currentGroup) {
    return (
      <Stack gap="xs">
        <Text size="sm" fw={500}>
          同義語グループ
        </Text>
        <Text size="xs" c="dimmed">
          この用語はまだ同義語グループに属していません
        </Text>
        <Button
          variant="light"
          size="xs"
          leftSection={<IconPlus size={14} />}
          onClick={handleCreateGroup}
          loading={isLoading}
        >
          同義語グループを作成
        </Button>
      </Stack>
    )
  }

  return (
    <Stack gap="xs">
      <Group justify="space-between">
        <Text size="sm" fw={500}>
          同義語グループ
        </Text>
        <Tooltip label="グループを削除">
          <ActionIcon
            variant="subtle"
            color="red"
            size="sm"
            onClick={() => onDeleteGroup(currentGroup.id)}
            aria-label="Delete synonym group"
          >
            <IconTrash size={14} />
          </ActionIcon>
        </Tooltip>
      </Group>

      <Text size="xs" c="dimmed">
        代表用語の名前で用語集に掲載されます
      </Text>

      <Stack gap={4}>
        {currentGroup.members.map((member) => {
          const isPrimary = member.term_text === currentGroup.primary_term_text
          return (
            <Group key={member.id} gap="xs" justify="space-between">
              <Group gap="xs">
                {isPrimary ? (
                  <IconStarFilled size={14} color="var(--mantine-color-yellow-6)" />
                ) : (
                  <Tooltip label="代表用語に設定">
                    <ActionIcon
                      variant="subtle"
                      size="xs"
                      onClick={() => onUpdatePrimary(currentGroup.id, member.term_text)}
                      aria-label="Set as primary"
                    >
                      <IconStar size={14} />
                    </ActionIcon>
                  </Tooltip>
                )}
                <Text size="sm">
                  {member.term_text}
                  {isPrimary && (
                    <Badge size="xs" variant="light" color="yellow" ml={4}>
                      代表
                    </Badge>
                  )}
                </Text>
              </Group>
              <Tooltip label="グループから解除">
                <ActionIcon
                  variant="subtle"
                  color="gray"
                  size="xs"
                  onClick={() => onRemoveMember(currentGroup.id, member.id)}
                  aria-label="Remove from group"
                >
                  <IconTrash size={14} />
                </ActionIcon>
              </Tooltip>
            </Group>
          )
        })}
      </Stack>

      <Group gap="xs">
        <Autocomplete
          placeholder="用語を追加..."
          data={availableTerms}
          value={addTermText}
          onChange={setAddTermText}
          size="xs"
          style={{ flex: 1 }}
        />
        <Button
          variant="light"
          size="xs"
          onClick={handleAddMember}
          disabled={!addTermText.trim()}
          loading={isLoading}
        >
          追加
        </Button>
      </Group>
    </Stack>
  )
}
