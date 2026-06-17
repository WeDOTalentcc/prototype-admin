"use client"

import React, { createContext, useContext, useMemo } from "react"
import type { UpdateFieldResult } from "@/hooks/candidates/use-candidate-field-update"

interface CandidateEditContextValue {
  /** Whether inline editing is enabled in this subtree. Default false. */
  editable: boolean
  /** Candidate id — required for save callback to know which candidate. */
  candidateId: string | undefined
  /** Save function — usually wired to useCandidateFieldUpdate.updateField */
  updateField?: (fieldName: string, value: string | number | null) => Promise<UpdateFieldResult>
  /** Saving-state lookup for a given field */
  isSaving?: (fieldName: string) => boolean
}

const CandidateEditContext = createContext<CandidateEditContextValue>({
  editable: false,
  candidateId: undefined,
})

interface CandidateEditProviderProps {
  editable: boolean
  candidateId: string | undefined
  updateField?: CandidateEditContextValue["updateField"]
  isSaving?: CandidateEditContextValue["isSaving"]
  children: React.ReactNode
}

/**
 * Provider exposed by Surface 2/3 (CandidatePage in mode='page' or via
 * explicit opt-in). Default behavior is editable=false (Surface 1
 * drawer = read-only).
 *
 * Consumers (ProfileInfoCards, CandidateContactActions, etc.) use
 * useCandidateEdit() to decide between display vs inline-edit rendering.
 */
export function CandidateEditProvider({
  editable,
  candidateId,
  updateField,
  isSaving,
  children,
}: CandidateEditProviderProps) {
  const value = useMemo(
    () => ({ editable, candidateId, updateField, isSaving }),
    [editable, candidateId, updateField, isSaving]
  )
  return <CandidateEditContext.Provider value={value}>{children}</CandidateEditContext.Provider>
}

export function useCandidateEdit(): CandidateEditContextValue {
  return useContext(CandidateEditContext)
}
