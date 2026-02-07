import { Button, Group, Modal, Stack, TextInput } from '@mantine/core'
import { useState } from 'react'

interface AddTermModalProps {
  opened: boolean
  onClose: () => void
  onSubmit: (termText: string) => void
  title: string
  placeholder: string
  isLoading: boolean
}

export function AddTermModal({
  opened,
  onClose,
  onSubmit,
  title,
  placeholder,
  isLoading,
}: AddTermModalProps) {
  const [termText, setTermText] = useState('')

  const handleSubmit = () => {
    if (!termText.trim()) return
    onSubmit(termText.trim())
    setTermText('')
  }

  const handleClose = () => {
    setTermText('')
    onClose()
  }

  return (
    <Modal opened={opened} onClose={handleClose} title={title}>
      <Stack>
        <TextInput
          label="用語"
          placeholder={placeholder}
          value={termText}
          onChange={(e) => setTermText(e.target.value)}
          required
        />
        <Group justify="flex-end">
          <Button variant="subtle" onClick={handleClose}>
            キャンセル
          </Button>
          <Button onClick={handleSubmit} loading={isLoading}>
            追加
          </Button>
        </Group>
      </Stack>
    </Modal>
  )
}
