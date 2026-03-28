"use client"

import { useState } from "react"

export interface SettingsFormState {
  hasChanges: boolean
}

export interface SettingsFormActions {
  setHasChanges: (changed: boolean) => void
  handleSave: () => void
  handleReset: () => void
}

export function useSettingsForm(): { state: SettingsFormState; actions: SettingsFormActions } {
  const [hasChanges, setHasChanges] = useState(false)

  const handleSave = () => {
    setHasChanges(false)
  }

  const handleReset = () => {
    setHasChanges(false)
  }

  return {
    state: { hasChanges },
    actions: { setHasChanges, handleSave, handleReset }
  }
}
