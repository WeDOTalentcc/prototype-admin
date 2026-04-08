"use client"

import { useEffect } from "react"
import { CURRENCY_SYMBOL } from "@/lib/pricing"
import { type FieldOrigin } from "../../job-creation/field-origin-badge"
import {
  type TechnicalSkill,
  type BehavioralCompetency,
  type SalaryInfo,
  type WSIQuestion,
  type BasicInfoFields,
  type WizardStage,
  INITIAL_GENERAL_MESSAGE,
} from '..'
import type { WizardMode } from '../types'
import type { DetectedCriteria } from '../ExpandedChatContext'
import { useChatSync, useToolCalling, useFieldHighlight } from '.'
import { useConversationMemory } from './useConversationMemory'
import { useLearning } from './useLearning'
import { useFastTrack } from '@/hooks/useFastTrack'
import { useJobWizard } from "@/hooks/use-lia-suggestions"
import { useJobWizardBackend } from "@/hooks/use-job-wizard-backend"
import { useProactiveHandlers, useGroupedPanelChangeHandler } from "./useExpandedChatCallbacks"
import { useWizardAnalytics } from './useWizardAnalytics'
import { useContextSwitching, type WizardSnapshot, type GeneralChatSnapshot } from './useContextSwitching'
import { useAnalyticsSession } from './useAnalyticsSession'
import { useConversationMemoryInit } from './useConversationMemoryInit'
import { useCompanyId } from '@/hooks/useCompanyId'
import type { Message, ExpandedChatModalProps } from '../types'

interface AuthUser {
  email?: string
  id?: string
  name?: string
}

interface UseExpandedChatCoreHooksParams {
  user: AuthUser | null
  isJobCreationMode: boolean
  isOpen: boolean
  mode: string
  messages: Message[]
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>
  currentStage: WizardStage
  setCurrentStage: React.Dispatch<React.SetStateAction<WizardStage>>
  detectedCriteria: DetectedCriteria
  setDetectedCriteria: React.Dispatch<React.SetStateAction<DetectedCriteria>>
  basicInfoFields: BasicInfoFields
  setBasicInfoFields: React.Dispatch<React.SetStateAction<BasicInfoFields>>
  setFieldOrigins: React.Dispatch<React.SetStateAction<Record<string, { source: FieldOrigin; confidence: number }>>>
  conversationId: string | null
  setConversationId: React.Dispatch<React.SetStateAction<string | null>>
  messagesEndRef: React.RefObject<HTMLDivElement | null>
  wizardMode: WizardMode
  setWizardMode: React.Dispatch<React.SetStateAction<WizardMode>>
  setTechnicalSkills: (skills: TechnicalSkill[]) => void
  setBehavioralCompetencies: (competencies: BehavioralCompetency[]) => void
  setSalaryInfo: (info: SalaryInfo) => void
  setWsiQuestions: (questions: WSIQuestion[]) => void
  setGeneratedJobDescription: React.Dispatch<React.SetStateAction<string>>
  setWizardFastTrackSourceJobId: (id: string | null) => void
  wizardDraftId: string
  fastTrackMessageSent: boolean
  setFastTrackMessageSent: (v: boolean) => void
  fastTrackSuggestionsShownTracked: boolean
  setFastTrackSuggestionsShownTracked: (v: boolean) => void
  awaitingFastTrackSelection: boolean
  setAwaitingFastTrackSelection: (v: boolean) => void
  resetFastTrackConversationState: () => void
  fastTrackHasSuggestions?: boolean
}

export function useExpandedChatCoreHooks(params: UseExpandedChatCoreHooksParams) {
  const {
    user, isJobCreationMode, isOpen, mode,
    messages, setMessages,
    currentStage, setCurrentStage,
    detectedCriteria, setDetectedCriteria,
    basicInfoFields, setBasicInfoFields, setFieldOrigins,
    conversationId, setConversationId, messagesEndRef,
    wizardMode, setWizardMode,
    setTechnicalSkills, setBehavioralCompetencies,
    setSalaryInfo, setWsiQuestions, setGeneratedJobDescription,
    setWizardFastTrackSourceJobId, wizardDraftId,
    fastTrackMessageSent, setFastTrackMessageSent,
    fastTrackSuggestionsShownTracked, setFastTrackSuggestionsShownTracked,
    setAwaitingFastTrackSelection,
    resetFastTrackConversationState,
  } = params

  const { companyId: resolvedCompanyId, isLoading: isLoadingTenant } = useCompanyId()
  const jobWizard = useJobWizard()

  const fastTrack = useFastTrack({
    companyId: resolvedCompanyId ?? '',
    debounceMs: 600,
    minSimilarity: 0.70,
  })

  const toolCalling = useToolCalling({
    onToolExecuted: (_result) => {},
    onToolError: (_error, _toolName) => {},
  })

  const conversationMemory = useConversationMemory({
    summaryThreshold: 10,
    maxMessages: 50,
    onError: (_error) => {},
    onConversationLoaded: (_conv) => {},
  })

  const {
    processStep: processBackendStep,
    isProcessing: isBackendProcessing,
    lastResponse: lastBackendResponse,
    callEvaluationStep,
    isEvaluating,
    evaluationResult,
    clearEvaluationResult,
    fetchDeduplicatedSkills,
    filterSkillSuggestions,
    isFetchingSkills
  } = useJobWizardBackend({
    companyId: resolvedCompanyId ?? '',
    onCriteriaDetected: (criteria, origins) => {
      if (criteria.job_title) {
        const jobTitle = criteria.job_title
        setDetectedCriteria((prev) => ({ ...prev, cargo: jobTitle }))
        setBasicInfoFields(prev => ({ ...prev, cargo: jobTitle }))
        fastTrack.searchWithDebounce(jobTitle, criteria.department)
      }
      if (criteria.seniority) {
        const seniority = criteria.seniority
        setDetectedCriteria((prev) => ({ ...prev, senioridadeIdiomas: seniority }))
      }
      if (criteria.technical_skills) {
        const skills = criteria.technical_skills
        setDetectedCriteria((prev) => ({ ...prev, competenciasTecnicas: skills }))
      }
      if (criteria.behavioral_skills) {
        const behaviors = criteria.behavioral_skills
        setDetectedCriteria((prev) => ({ ...prev, competenciasComportamentais: behaviors }))
      }
      if (criteria.salary_min || criteria.salary_max) {
        setDetectedCriteria((prev) => ({
          ...prev,
          salario: `${CURRENCY_SYMBOL} ${criteria.salary_min?.toLocaleString() || '?'} - ${CURRENCY_SYMBOL} ${criteria.salary_max?.toLocaleString() || '?'}`
        }))
      }
      if (criteria.location) {
        setBasicInfoFields(prev => ({ ...prev, localidade: criteria.location! }))
      }
      if (criteria.work_model) {
        setBasicInfoFields(prev => ({ ...prev, modeloTrabalho: criteria.work_model! }))
      }
      const newOrigins: Record<string, { source: FieldOrigin; confidence: number }> = {}
      for (const [field, data] of Object.entries(origins)) {
        newOrigins[field] = {
          source: (data as { source?: FieldOrigin; confidence?: number }).source || 'detected',
          confidence: (data as { source?: FieldOrigin; confidence?: number }).confidence || 0.7
        }
      }
      setFieldOrigins(prev => ({ ...prev, ...newOrigins }))
    },
    onError: (_error) => {}
  })

  const { handleProactiveAccept, handleProactiveReject } = useProactiveHandlers({ user: user as Record<string, unknown> | null, setMessages })
  const { handleGroupedPanelChange } = useGroupedPanelChangeHandler({ setMessages })

  const {
    trackFieldChange,
    generateLLMContext,
    clearChanges: clearChatSyncChanges,
  } = useChatSync({
    debounceMs: 800,
    groupingWindowMs: 1500,
    onGroupedChange: handleGroupedPanelChange,
  })

  const {
    highlightField,
    isHighlighted,
    highlightedFields,
    clearAllHighlights,
  } = useFieldHighlight({ highlightDurationMs: 2000 })

  const learning = useLearning()
  const analytics = useWizardAnalytics('default-company', 'default-recruiter')

  const contextSwitching = useContextSwitching({
    autoDetectIntent: true,
    onContextSwitch: (_from, to) => {
      if (to === 'wizard') {
        setWizardMode('pre_wizard')
      } else if (to === 'general') {
        setWizardMode('general')
      } else if (to === 'fast_track') {
        setWizardMode('fast_track')
      }
    },
    onWizardRestore: (snapshot: WizardSnapshot) => {
      if (snapshot.stage) setCurrentStage(snapshot.stage as WizardStage)
      if (snapshot.basicInfoFields) setBasicInfoFields(snapshot.basicInfoFields as unknown as BasicInfoFields)
      if (snapshot.technicalSkills && Array.isArray(snapshot.technicalSkills)) setTechnicalSkills(snapshot.technicalSkills as TechnicalSkill[])
      if (snapshot.behavioralCompetencies && Array.isArray(snapshot.behavioralCompetencies)) setBehavioralCompetencies(snapshot.behavioralCompetencies as BehavioralCompetency[])
      if (snapshot.salaryInfo) setSalaryInfo(snapshot.salaryInfo as unknown as SalaryInfo)
      if (snapshot.wsiQuestions && Array.isArray(snapshot.wsiQuestions)) setWsiQuestions(snapshot.wsiQuestions as WSIQuestion[])
      if (snapshot.generatedJobDescription) setGeneratedJobDescription(snapshot.generatedJobDescription)
      if (snapshot.fastTrackSourceJobId) setWizardFastTrackSourceJobId(snapshot.fastTrackSourceJobId)
    },
    onGeneralRestore: (snapshot: GeneralChatSnapshot) => {
      if (snapshot.conversationId) {
        setConversationId(snapshot.conversationId)
        if (user?.email) {
          (async () => {
            try {
              await conversationMemory.initConversation(user.email ?? '', 'general')
              if (conversationMemory.messages.length > 0) {
                const restoredMessages: Message[] = conversationMemory.messages.map(m => ({
                  id: m.id || `restored-${Date.now()}-${Math.random()}`,
                  role: m.role as 'user' | 'assistant',
                  content: m.content,
                  timestamp: m.created_at ? new Date(m.created_at) : new Date(),
                }))
                const hasInitialMessage = restoredMessages.some(m =>
                  m.role === 'assistant' && m.content.includes('Olá!')
                )
                if (!hasInitialMessage) {
                  const initialMsg: Message = {
                    id: 'initial-restored',
                    role: 'assistant',
                    content: INITIAL_GENERAL_MESSAGE,
                    timestamp: new Date(Date.now() - 1000),
                  }
                  setMessages([initialMsg, ...restoredMessages])
                } else {
                  setMessages(restoredMessages)
                }
              }
            } catch (_error) {}
          })()
        }
      }
      if (snapshot.lastMessageIndex > 0) {
        setTimeout(() => {
          messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
        }, 0)
      }
    },
  })

  const { syncContext } = contextSwitching
  useEffect(() => {
    (syncContext as (mode: unknown, opts: Record<string, unknown>) => void)(wizardMode, { skipCallbacks: true, skipSnapshotRestore: true })
  }, [wizardMode, syncContext])

  useAnalyticsSession({ analytics, isOpen, mode })
  useConversationMemoryInit({ conversationMemory: conversationMemory as unknown as Parameters<typeof useConversationMemoryInit>[0]['conversationMemory'], isOpen, mode, user, wizardDraftId })

  const { fetchWizardSuggestions } = learning
  useEffect(() => {
    if (detectedCriteria?.cargo && mode === 'job-creation') {
      fetchWizardSuggestions({
        companyId: resolvedCompanyId || '',
        jobTitle: detectedCriteria.cargo,
        department: detectedCriteria.departamento || undefined,
        seniority: undefined
      })
    }
  }, [detectedCriteria?.cargo, detectedCriteria?.departamento, mode, fetchWizardSuggestions, resolvedCompanyId])

  const {
    clearSuggestions: clearFastTrackSuggestions,
    hasSuggestions: fastTrackHasSuggestions,
    suggestions: fastTrackSuggestions,
    getLiaMessage: getFastTrackLiaMessage
  } = fastTrack

  useEffect(() => {
    if (fastTrackHasSuggestions && !fastTrackMessageSent && mode === 'job-creation' && currentStage === 'input-evaluation') {
      const liaMessage = getFastTrackLiaMessage(fastTrackSuggestions)
      if (liaMessage) {
        const fastTrackMessage = {
          id: `fasttrack-${Date.now()}`,
          role: 'assistant' as const,
          content: liaMessage,
          timestamp: new Date(),
        }
        setMessages(prev => [...prev, fastTrackMessage])
        setFastTrackMessageSent(true)
        if (!fastTrackSuggestionsShownTracked) {
          analytics.trackSuggestion('fast_track_suggestion_shown', false)
          setFastTrackSuggestionsShownTracked(true)
        }
      }
    }
  }, [fastTrackHasSuggestions, fastTrackSuggestions, fastTrackMessageSent, mode, currentStage, analytics, fastTrackSuggestionsShownTracked, getFastTrackLiaMessage, setFastTrackMessageSent, setFastTrackSuggestionsShownTracked, setMessages])

  useEffect(() => {
    if (!isOpen || mode !== 'job-creation') {
      resetFastTrackConversationState()
      clearFastTrackSuggestions()
    }
  }, [isOpen, mode, clearFastTrackSuggestions, resetFastTrackConversationState, setAwaitingFastTrackSelection, setFastTrackMessageSent])

  useEffect(() => {
    if (!fastTrackHasSuggestions) {
      setAwaitingFastTrackSelection(false)
      setFastTrackMessageSent(false)
    }
  }, [fastTrackHasSuggestions, setAwaitingFastTrackSelection, setFastTrackMessageSent])

  return {
    jobWizard,
    fastTrack,
    toolCalling,
    conversationMemory,
    callEvaluationStep,
    isEvaluating,
    evaluationResult,
    clearEvaluationResult,
    fetchDeduplicatedSkills,
    filterSkillSuggestions,
    isFetchingSkills,
    processBackendStep,
    isBackendProcessing,
    lastBackendResponse,
    handleProactiveAccept,
    handleProactiveReject,
    trackFieldChange,
    generateLLMContext,
    clearChatSyncChanges,
    highlightField,
    isHighlighted,
    highlightedFields,
    clearAllHighlights,
    learning,
    analytics,
    contextSwitching,
  }
}
