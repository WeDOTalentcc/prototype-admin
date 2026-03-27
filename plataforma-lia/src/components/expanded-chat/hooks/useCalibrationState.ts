/**
 * useCalibrationState
 *
 * Sprint 4.2 — 2026-03-27
 * Encapsula os ~23 estados relacionados ao fluxo de Calibração (Stage 8).
 * Inclui: candidatos, aprovações/rejeições, busca global, pós-calibração.
 * Padrão { state, actions } compatível com Pinia stores (Vue 3).
 */

import { useState, useRef } from 'react'
import type { CalibrationCandidate } from '../types'

export interface CalibrationStateValues {
  calibrationCandidates: CalibrationCandidate[]
  currentCalibrationIndex: number
  approvedCandidates: string[]
  rejectedCandidates: string[]
  calibrationComplete: boolean
  isLoadingCalibration: boolean
  showCalibrationModal: boolean
  calibrationSessionId: string | null
  awaitingCalibrationChoice: boolean
  showEditCriteriaModal: boolean
  candidateProfileTab: 'experience' | 'education' | 'skillmap'
  calibrationComment: string
  publishedJobId: string | null
  calibrationCriteria: { id: string; text: string; source: 'technical' | 'behavioral' }[]
  postCalibrationProcessing: boolean
  localCandidateCount: number
  globalSearchAuthorized: boolean
  postCalibrationComplete: boolean
  hasAttemptedCalibrationGeneration: boolean
  searchPhase: 'idle' | 'local-searching' | 'local-complete' | 'global-searching' | 'global-complete'
  globalCandidateCount: number
  preferredCandidateCount: number
  showClearDraftConfirm: boolean
}

export interface CalibrationStateActions {
  setCalibrationCandidates: React.Dispatch<React.SetStateAction<CalibrationCandidate[]>>
  setCurrentCalibrationIndex: React.Dispatch<React.SetStateAction<number>>
  setApprovedCandidates: React.Dispatch<React.SetStateAction<string[]>>
  setRejectedCandidates: React.Dispatch<React.SetStateAction<string[]>>
  setCalibrationComplete: React.Dispatch<React.SetStateAction<boolean>>
  setIsLoadingCalibration: React.Dispatch<React.SetStateAction<boolean>>
  setShowCalibrationModal: React.Dispatch<React.SetStateAction<boolean>>
  setCalibrationSessionId: React.Dispatch<React.SetStateAction<string | null>>
  setAwaitingCalibrationChoice: React.Dispatch<React.SetStateAction<boolean>>
  setShowEditCriteriaModal: React.Dispatch<React.SetStateAction<boolean>>
  setCandidateProfileTab: React.Dispatch<React.SetStateAction<CalibrationStateValues['candidateProfileTab']>>
  setCalibrationComment: React.Dispatch<React.SetStateAction<string>>
  setPublishedJobId: React.Dispatch<React.SetStateAction<string | null>>
  setCalibrationCriteria: React.Dispatch<React.SetStateAction<CalibrationStateValues['calibrationCriteria']>>
  setPostCalibrationProcessing: React.Dispatch<React.SetStateAction<boolean>>
  setLocalCandidateCount: React.Dispatch<React.SetStateAction<number>>
  setGlobalSearchAuthorized: React.Dispatch<React.SetStateAction<boolean>>
  setPostCalibrationComplete: React.Dispatch<React.SetStateAction<boolean>>
  setHasAttemptedCalibrationGeneration: React.Dispatch<React.SetStateAction<boolean>>
  setSearchPhase: React.Dispatch<React.SetStateAction<CalibrationStateValues['searchPhase']>>
  setGlobalCandidateCount: React.Dispatch<React.SetStateAction<number>>
  setPreferredCandidateCount: React.Dispatch<React.SetStateAction<number>>
  setShowClearDraftConfirm: React.Dispatch<React.SetStateAction<boolean>>
  resetCalibrationState: () => void
}

export interface UseCalibrationStateReturn {
  state: CalibrationStateValues
  actions: CalibrationStateActions
  /** Ref para evitar loop infinito ao checar se calibração já foi gerada */
  postCalibrationFlowStartedRef: React.MutableRefObject<boolean>
}

export function useCalibrationState(): UseCalibrationStateReturn {
  const [calibrationCandidates, setCalibrationCandidates] = useState<CalibrationCandidate[]>([])
  const [currentCalibrationIndex, setCurrentCalibrationIndex] = useState(0)
  const [approvedCandidates, setApprovedCandidates] = useState<string[]>([])
  const [rejectedCandidates, setRejectedCandidates] = useState<string[]>([])
  const [calibrationComplete, setCalibrationComplete] = useState(false)
  const [isLoadingCalibration, setIsLoadingCalibration] = useState(false)
  const [showCalibrationModal, setShowCalibrationModal] = useState(false)
  const [calibrationSessionId, setCalibrationSessionId] = useState<string | null>(null)
  const [awaitingCalibrationChoice, setAwaitingCalibrationChoice] = useState(false)
  const [showEditCriteriaModal, setShowEditCriteriaModal] = useState(false)
  const [candidateProfileTab, setCandidateProfileTab] = useState<CalibrationStateValues['candidateProfileTab']>('experience')
  const [calibrationComment, setCalibrationComment] = useState('')
  const [publishedJobId, setPublishedJobId] = useState<string | null>(null)
  const [calibrationCriteria, setCalibrationCriteria] = useState<CalibrationStateValues['calibrationCriteria']>([])
  const [postCalibrationProcessing, setPostCalibrationProcessing] = useState(false)
  const [localCandidateCount, setLocalCandidateCount] = useState(0)
  const [globalSearchAuthorized, setGlobalSearchAuthorized] = useState(false)
  const [postCalibrationComplete, setPostCalibrationComplete] = useState(false)
  const [hasAttemptedCalibrationGeneration, setHasAttemptedCalibrationGeneration] = useState(false)
  const [searchPhase, setSearchPhase] = useState<CalibrationStateValues['searchPhase']>('idle')
  const [globalCandidateCount, setGlobalCandidateCount] = useState(0)
  const [preferredCandidateCount, setPreferredCandidateCount] = useState(3)
  const [showClearDraftConfirm, setShowClearDraftConfirm] = useState(false)

  const postCalibrationFlowStartedRef = useRef(false)

  const resetCalibrationState = () => {
    setCalibrationCandidates([])
    setCurrentCalibrationIndex(0)
    setApprovedCandidates([])
    setRejectedCandidates([])
    setCalibrationComplete(false)
    setIsLoadingCalibration(false)
    setShowCalibrationModal(false)
    setCalibrationSessionId(null)
    setAwaitingCalibrationChoice(false)
    setShowEditCriteriaModal(false)
    setCandidateProfileTab('experience')
    setCalibrationComment('')
    setPublishedJobId(null)
    setCalibrationCriteria([])
    setPostCalibrationProcessing(false)
    setLocalCandidateCount(0)
    setGlobalSearchAuthorized(false)
    setPostCalibrationComplete(false)
    setHasAttemptedCalibrationGeneration(false)
    setSearchPhase('idle')
    setGlobalCandidateCount(0)
    setPreferredCandidateCount(3)
    setShowClearDraftConfirm(false)
    postCalibrationFlowStartedRef.current = false
  }

  return {
    state: {
      calibrationCandidates,
      currentCalibrationIndex,
      approvedCandidates,
      rejectedCandidates,
      calibrationComplete,
      isLoadingCalibration,
      showCalibrationModal,
      calibrationSessionId,
      awaitingCalibrationChoice,
      showEditCriteriaModal,
      candidateProfileTab,
      calibrationComment,
      publishedJobId,
      calibrationCriteria,
      postCalibrationProcessing,
      localCandidateCount,
      globalSearchAuthorized,
      postCalibrationComplete,
      hasAttemptedCalibrationGeneration,
      searchPhase,
      globalCandidateCount,
      preferredCandidateCount,
      showClearDraftConfirm,
    },
    actions: {
      setCalibrationCandidates,
      setCurrentCalibrationIndex,
      setApprovedCandidates,
      setRejectedCandidates,
      setCalibrationComplete,
      setIsLoadingCalibration,
      setShowCalibrationModal,
      setCalibrationSessionId,
      setAwaitingCalibrationChoice,
      setShowEditCriteriaModal,
      setCandidateProfileTab,
      setCalibrationComment,
      setPublishedJobId,
      setCalibrationCriteria,
      setPostCalibrationProcessing,
      setLocalCandidateCount,
      setGlobalSearchAuthorized,
      setPostCalibrationComplete,
      setHasAttemptedCalibrationGeneration,
      setSearchPhase,
      setGlobalCandidateCount,
      setPreferredCandidateCount,
      setShowClearDraftConfirm,
      resetCalibrationState,
    },
    postCalibrationFlowStartedRef,
  }
}
