import { useState, useCallback } from 'react'

interface UseEditLockOptions {
  onSave?: () => Promise<void> | void
  onCancel?: () => void
}

interface UseEditLockReturn {
  isEditing: boolean
  isSaving: boolean
  startEditing: () => void
  cancelEditing: () => void
  saveAndExit: () => Promise<void>
}

export function useEditLock(options: UseEditLockOptions = {}): UseEditLockReturn {
  const [isEditing, setIsEditing] = useState(false)
  const [isSaving, setIsSaving] = useState(false)

  const startEditing = useCallback(() => {
    setIsEditing(true)
  }, [])

  const cancelEditing = useCallback(() => {
    setIsEditing(false)
    options.onCancel?.()
  }, [options])

  const saveAndExit = useCallback(async () => {
    setIsSaving(true)
    try {
      await options.onSave?.()
      setIsEditing(false)
    } finally {
      setIsSaving(false)
    }
  }, [options])

  return {
    isEditing,
    isSaving,
    startEditing,
    cancelEditing,
    saveAndExit,
  }
}

export type { UseEditLockReturn }
