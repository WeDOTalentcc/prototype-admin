/**
 * useFastTrackState
 *
 * Sprint 4.2 — 2026-03-27
 * Encapsula os ~16 estados do fluxo Fast Track (busca semântica de vagas similares).
 * Inclui: modo wizard, estado da busca, seleção de vagas, confirmações pendentes.
 * Padrão { state, actions } compatível com Pinia stores (Vue 3).
 */

import { useState, useCallback } from 'react'
import type { WizardMode, FastTrackState } from '../types'
import type { VacancySummary } from '../../job-creation/vacancy-search-results'
import type { VacancyFullDetails } from '../../job-creation/vacancy-full-summary'
import type { VacancyAdjustments, VacancySearchCriteria } from '@/services/lia-api'

export type { VacancyAdjustments, VacancySearchCriteria }

export interface FastTrackAppliedData {
  gestor: string
  localidade: string
  sourceJobTitle: string
}

export interface FastTrackOriginalCompetencies {
  technicalSkillNames: string[]
  behavioralCompetencyNames: string[]
}

export interface FastTrackStateValues {
  wizardMode: WizardMode
  fastTrackState: FastTrackState
  fastTrackSearchResults: VacancySummary[]
  fastTrackSelectedVacancy: VacancyFullDetails | null
  fastTrackAdjustments: VacancyAdjustments
  fastTrackSearchCriteria: VacancySearchCriteria
  isSearchingVacancies: boolean
  wizardFastTrackSourceJobId: string | null
  fastTrackMessageSent: boolean
  fastTrackSuggestionsShownTracked: boolean
  awaitingFastTrackSelection: boolean
  awaitingSensitiveFieldsConfirmation: boolean
  fastTrackAppliedData: FastTrackAppliedData | null
  fastTrackOriginalCompetencies: FastTrackOriginalCompetencies | null
  wsiRegenerationPrompted: boolean
  awaitingWSIRegenerationConfirmation: boolean
}

export interface FastTrackStateActions {
  setWizardMode: React.Dispatch<React.SetStateAction<WizardMode>>
  setFastTrackState: React.Dispatch<React.SetStateAction<FastTrackState>>
  setFastTrackSearchResults: React.Dispatch<React.SetStateAction<VacancySummary[]>>
  setFastTrackSelectedVacancy: React.Dispatch<React.SetStateAction<VacancyFullDetails | null>>
  setFastTrackAdjustments: React.Dispatch<React.SetStateAction<VacancyAdjustments>>
  setFastTrackSearchCriteria: React.Dispatch<React.SetStateAction<VacancySearchCriteria>>
  setIsSearchingVacancies: React.Dispatch<React.SetStateAction<boolean>>
  setWizardFastTrackSourceJobId: React.Dispatch<React.SetStateAction<string | null>>
  setFastTrackMessageSent: React.Dispatch<React.SetStateAction<boolean>>
  setFastTrackSuggestionsShownTracked: React.Dispatch<React.SetStateAction<boolean>>
  setAwaitingFastTrackSelection: React.Dispatch<React.SetStateAction<boolean>>
  setAwaitingSensitiveFieldsConfirmation: React.Dispatch<React.SetStateAction<boolean>>
  setFastTrackAppliedData: React.Dispatch<React.SetStateAction<FastTrackAppliedData | null>>
  setFastTrackOriginalCompetencies: React.Dispatch<React.SetStateAction<FastTrackOriginalCompetencies | null>>
  setWsiRegenerationPrompted: React.Dispatch<React.SetStateAction<boolean>>
  setAwaitingWSIRegenerationConfirmation: React.Dispatch<React.SetStateAction<boolean>>
  resetFastTrackConversationState: () => void
  resetFastTrackFullState: () => void
}

export interface UseFastTrackStateReturn {
  state: FastTrackStateValues
  actions: FastTrackStateActions
}

export function useFastTrackState(): UseFastTrackStateReturn {
  const [wizardMode, setWizardMode] = useState<WizardMode>('pre_wizard')
  const [fastTrackState, setFastTrackState] = useState<FastTrackState>('initial')
  const [fastTrackSearchResults, setFastTrackSearchResults] = useState<VacancySummary[]>([])
  const [fastTrackSelectedVacancy, setFastTrackSelectedVacancy] = useState<VacancyFullDetails | null>(null)
  const [fastTrackAdjustments, setFastTrackAdjustments] = useState<VacancyAdjustments>({})
  const [fastTrackSearchCriteria, setFastTrackSearchCriteria] = useState<VacancySearchCriteria>({})
  const [isSearchingVacancies, setIsSearchingVacancies] = useState(false)
  const [wizardFastTrackSourceJobId, setWizardFastTrackSourceJobId] = useState<string | null>(null)
  const [fastTrackMessageSent, setFastTrackMessageSent] = useState(false)
  const [fastTrackSuggestionsShownTracked, setFastTrackSuggestionsShownTracked] = useState(false)
  const [awaitingFastTrackSelection, setAwaitingFastTrackSelection] = useState(false)
  const [awaitingSensitiveFieldsConfirmation, setAwaitingSensitiveFieldsConfirmation] = useState(false)
  const [fastTrackAppliedData, setFastTrackAppliedData] = useState<FastTrackAppliedData | null>(null)
  const [fastTrackOriginalCompetencies, setFastTrackOriginalCompetencies] = useState<FastTrackOriginalCompetencies | null>(null)
  const [wsiRegenerationPrompted, setWsiRegenerationPrompted] = useState(false)
  const [awaitingWSIRegenerationConfirmation, setAwaitingWSIRegenerationConfirmation] = useState(false)

  const resetFastTrackConversationState = useCallback(() => {
    setFastTrackMessageSent(false)
    setFastTrackSuggestionsShownTracked(false)
    setAwaitingFastTrackSelection(false)
    setAwaitingSensitiveFieldsConfirmation(false)
    setFastTrackAppliedData(null)
    setFastTrackOriginalCompetencies(null)
    setWsiRegenerationPrompted(false)
    setAwaitingWSIRegenerationConfirmation(false)
  }, [])

  const resetFastTrackFullState = useCallback(() => {
    resetFastTrackConversationState()
    setWizardMode('pre_wizard')
    setFastTrackState('initial')
    setFastTrackSearchResults([])
    setFastTrackSelectedVacancy(null)
    setFastTrackAdjustments({})
    setFastTrackSearchCriteria({})
    setIsSearchingVacancies(false)
    setWizardFastTrackSourceJobId(null)
  }, [resetFastTrackConversationState])

  return {
    state: {
      wizardMode,
      fastTrackState,
      fastTrackSearchResults,
      fastTrackSelectedVacancy,
      fastTrackAdjustments,
      fastTrackSearchCriteria,
      isSearchingVacancies,
      wizardFastTrackSourceJobId,
      fastTrackMessageSent,
      fastTrackSuggestionsShownTracked,
      awaitingFastTrackSelection,
      awaitingSensitiveFieldsConfirmation,
      fastTrackAppliedData,
      fastTrackOriginalCompetencies,
      wsiRegenerationPrompted,
      awaitingWSIRegenerationConfirmation,
    },
    actions: {
      setWizardMode,
      setFastTrackState,
      setFastTrackSearchResults,
      setFastTrackSelectedVacancy,
      setFastTrackAdjustments,
      setFastTrackSearchCriteria,
      setIsSearchingVacancies,
      setWizardFastTrackSourceJobId,
      setFastTrackMessageSent,
      setFastTrackSuggestionsShownTracked,
      setAwaitingFastTrackSelection,
      setAwaitingSensitiveFieldsConfirmation,
      setFastTrackAppliedData,
      setFastTrackOriginalCompetencies,
      setWsiRegenerationPrompted,
      setAwaitingWSIRegenerationConfirmation,
      resetFastTrackConversationState,
      resetFastTrackFullState,
    },
  }
}
