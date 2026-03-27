/**
 * useWSIState
 *
 * Sprint 4.2 — 2026-03-27
 * Encapsula os ~11 estados relacionados a WSI Questions (Stage 6).
 * Padrão { state, actions } compatível com Pinia stores (Vue 3).
 * Sem dependências React além de useState — sem JSX, sem business logic.
 */

import { useState } from 'react'
import type { WSIQuestion } from '../ExpandedChatContext'
import type { WSIQuestionCandidate } from '../types'

export interface WSIStateValues {
  wsiQuestions: WSIQuestion[]
  wsiCandidates: WSIQuestionCandidate[]
  wsiGenerationBatch: number
  isGeneratingWSI: boolean
  wsiHasGenerated: boolean
  useCompanyQuestions: boolean
  companyDefaultQuestions: {
    id: string
    question: string
    type: 'yes-no' | 'numeric' | 'open' | 'multiple-choice'
    enabled: boolean
    fromConfig: boolean
  }[]
  showCustomQuestionForm: boolean
  customQuestionText: string
  customQuestionType: 'open' | 'yes-no' | 'numeric' | 'multiple-choice'
  customQuestionRequired: boolean
}

export interface WSIStateActions {
  setWsiQuestions: React.Dispatch<React.SetStateAction<WSIQuestion[]>>
  setWsiCandidates: React.Dispatch<React.SetStateAction<WSIQuestionCandidate[]>>
  setWsiGenerationBatch: React.Dispatch<React.SetStateAction<number>>
  setIsGeneratingWSI: React.Dispatch<React.SetStateAction<boolean>>
  setWsiHasGenerated: React.Dispatch<React.SetStateAction<boolean>>
  setUseCompanyQuestions: React.Dispatch<React.SetStateAction<boolean>>
  setCompanyDefaultQuestions: React.Dispatch<React.SetStateAction<WSIStateValues['companyDefaultQuestions']>>
  setShowCustomQuestionForm: React.Dispatch<React.SetStateAction<boolean>>
  setCustomQuestionText: React.Dispatch<React.SetStateAction<string>>
  setCustomQuestionType: React.Dispatch<React.SetStateAction<WSIStateValues['customQuestionType']>>
  setCustomQuestionRequired: React.Dispatch<React.SetStateAction<boolean>>
  resetCustomQuestionForm: () => void
  resetWSIState: () => void
}

export interface UseWSIStateReturn {
  state: WSIStateValues
  actions: WSIStateActions
}

export function useWSIState(): UseWSIStateReturn {
  const [wsiQuestions, setWsiQuestions] = useState<WSIQuestion[]>([])
  const [wsiCandidates, setWsiCandidates] = useState<WSIQuestionCandidate[]>([])
  const [wsiGenerationBatch, setWsiGenerationBatch] = useState(0)
  const [isGeneratingWSI, setIsGeneratingWSI] = useState(false)
  const [wsiHasGenerated, setWsiHasGenerated] = useState(false)
  const [useCompanyQuestions, setUseCompanyQuestions] = useState(false)
  const [companyDefaultQuestions, setCompanyDefaultQuestions] = useState<WSIStateValues['companyDefaultQuestions']>([])
  const [showCustomQuestionForm, setShowCustomQuestionForm] = useState(false)
  const [customQuestionText, setCustomQuestionText] = useState('')
  const [customQuestionType, setCustomQuestionType] = useState<WSIStateValues['customQuestionType']>('open')
  const [customQuestionRequired, setCustomQuestionRequired] = useState(false)

  const resetCustomQuestionForm = () => {
    setShowCustomQuestionForm(false)
    setCustomQuestionText('')
    setCustomQuestionType('open')
    setCustomQuestionRequired(false)
  }

  const resetWSIState = () => {
    setWsiQuestions([])
    setWsiCandidates([])
    setWsiGenerationBatch(0)
    setIsGeneratingWSI(false)
    setWsiHasGenerated(false)
    setUseCompanyQuestions(false)
    setCompanyDefaultQuestions([])
    resetCustomQuestionForm()
  }

  return {
    state: {
      wsiQuestions,
      wsiCandidates,
      wsiGenerationBatch,
      isGeneratingWSI,
      wsiHasGenerated,
      useCompanyQuestions,
      companyDefaultQuestions,
      showCustomQuestionForm,
      customQuestionText,
      customQuestionType,
      customQuestionRequired,
    },
    actions: {
      setWsiQuestions,
      setWsiCandidates,
      setWsiGenerationBatch,
      setIsGeneratingWSI,
      setWsiHasGenerated,
      setUseCompanyQuestions,
      setCompanyDefaultQuestions,
      setShowCustomQuestionForm,
      setCustomQuestionText,
      setCustomQuestionType,
      setCustomQuestionRequired,
      resetCustomQuestionForm,
      resetWSIState,
    },
  }
}
