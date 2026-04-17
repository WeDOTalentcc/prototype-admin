'use client'

import React, { createContext, useContext, useState, useCallback, useEffect, ReactNode } from 'react'
import { useWizardStore } from '@/stores/wizard-store'
import type {
  WizardStage,
  TechnicalSkill,
  BehavioralCompetency,
  SalaryInfo,
  WSIQuestion,
  WSIQuestionCandidate,
  CalibrationCandidate,
  DetectedCriteria,
  BasicInfoFields,
  JobConfig,
  PublishingPlatform,
  CompanyConfig,
  SalaryBenchmark,
  Message,
  FieldOrigin,
  CompanyDefaultQuestion,
  WSIDroppedQuestion,
  WSIFairnessWarning
} from './types'
import {
  WIZARD_STAGES,
  INITIAL_BENEFITS,
  INITIAL_BEHAVIORAL_COMPETENCIES,
  INITIAL_PUBLISHING_PLATFORMS,
  AUTO_ADVANCE_CONFIDENCE_THRESHOLDS
} from './constants'
import { useCompanyBenefits } from '@/hooks/company/useCompanyBenefits'
import type { JobBenefit } from '@/types/benefits'

interface WizardContextValue {
  // Stage navigation
  currentStage: WizardStage
  setCurrentStage: (stage: WizardStage) => void
  goToNextStage: () => void
  goToPreviousStage: () => void
  canAdvance: boolean
  currentStageIndex: number
  
  // Messages
  messages: Message[]
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>
  addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => void
  
  // Detected criteria
  detectedCriteria: DetectedCriteria
  setDetectedCriteria: React.Dispatch<React.SetStateAction<DetectedCriteria>>
  
  // Basic info
  basicInfoFields: BasicInfoFields
  setBasicInfoFields: React.Dispatch<React.SetStateAction<BasicInfoFields>>
  
  // Technical skills
  technicalSkills: TechnicalSkill[]
  setTechnicalSkills: React.Dispatch<React.SetStateAction<TechnicalSkill[]>>
  addTechnicalSkill: (skill: TechnicalSkill) => void
  removeTechnicalSkill: (id: string) => void
  updateTechnicalSkill: (id: string, updates: Partial<TechnicalSkill>) => void
  
  // Behavioral competencies
  behavioralCompetencies: BehavioralCompetency[]
  setBehavioralCompetencies: React.Dispatch<React.SetStateAction<BehavioralCompetency[]>>
  toggleBehavioralCompetency: (id: string) => void
  updateBehavioralCompetency: (id: string, updates: Partial<BehavioralCompetency>) => void
  
  // Salary info
  salaryInfo: SalaryInfo
  setSalaryInfo: React.Dispatch<React.SetStateAction<SalaryInfo>>
  salaryBenchmark: SalaryBenchmark | null
  setSalaryBenchmark: React.Dispatch<React.SetStateAction<SalaryBenchmark | null>>
  
  // WSI Questions
  wsiQuestions: WSIQuestion[]
  setWsiQuestions: React.Dispatch<React.SetStateAction<WSIQuestion[]>>
  wsiCandidates: WSIQuestionCandidate[]
  setWsiCandidates: React.Dispatch<React.SetStateAction<WSIQuestionCandidate[]>>
  toggleWSIQuestionSelection: (id: string) => void
  deleteWSIQuestion: (id: string) => void
  updateWSIQuestionExpectedAnswer: (id: string, answer: unknown) => void
  isGeneratingWSI: boolean
  setIsGeneratingWSI: React.Dispatch<React.SetStateAction<boolean>>
  companyDefaultQuestions: CompanyDefaultQuestion[]
  setCompanyDefaultQuestions: React.Dispatch<React.SetStateAction<CompanyDefaultQuestion[]>>
  /**
   * Questions removed from the generated WSI set by the FairnessGuard
   * post-check. The wizard renders an inline warning so the recruiter can
   * see exactly which questions were dropped and why, instead of the count
   * shrinking silently. Wired by the WS payload handler when present.
   */
  wsiDroppedQuestions: WSIDroppedQuestion[]
  setWsiDroppedQuestions: React.Dispatch<React.SetStateAction<WSIDroppedQuestion[]>>
  wsiFairnessWarning: WSIFairnessWarning | null
  setWsiFairnessWarning: React.Dispatch<React.SetStateAction<WSIFairnessWarning | null>>
  
  // Calibration
  calibrationCandidates: CalibrationCandidate[]
  setCalibrationCandidates: React.Dispatch<React.SetStateAction<CalibrationCandidate[]>>
  currentCalibrationIndex: number
  setCurrentCalibrationIndex: React.Dispatch<React.SetStateAction<number>>
  approvedCandidates: string[]
  setApprovedCandidates: React.Dispatch<React.SetStateAction<string[]>>
  rejectedCandidates: string[]
  setRejectedCandidates: React.Dispatch<React.SetStateAction<string[]>>
  
  // Publishing
  publishingPlatforms: PublishingPlatform[]
  setPublishingPlatforms: React.Dispatch<React.SetStateAction<PublishingPlatform[]>>
  togglePlatform: (id: string) => void
  
  // Job config
  jobConfig: JobConfig
  setJobConfig: React.Dispatch<React.SetStateAction<JobConfig>>
  
  // Job description
  jobDescription: string
  setJobDescription: React.Dispatch<React.SetStateAction<string>>
  isGeneratingDescription: boolean
  setIsGeneratingDescription: React.Dispatch<React.SetStateAction<boolean>>
  
  // Company config
  companyConfig: CompanyConfig | null
  setCompanyConfig: React.Dispatch<React.SetStateAction<CompanyConfig | null>>
  
  // Field origins
  fieldOrigins: Record<string, { source: FieldOrigin; confidence: number }>
  setFieldOrigins: React.Dispatch<React.SetStateAction<Record<string, { source: FieldOrigin; confidence: number }>>>
  
  // Draft management
  wizardDraftId: string
  publishedJobId: string | null
  setPublishedJobId: React.Dispatch<React.SetStateAction<string | null>>
  
  // UI states
  competenciesTab: 'technical' | 'behavioral'
  setCompetenciesTab: React.Dispatch<React.SetStateAction<'technical' | 'behavioral'>>
  
  // Auto-advance helpers
  shouldAutoAdvance: (confidence: number) => boolean
  
  // Reset wizard
  resetWizard: () => void
}

const WizardContext = createContext<WizardContextValue | null>(null)

interface WizardProviderProps {
  children: ReactNode
  initialStage?: WizardStage
  companyId?: string
}

export function WizardProvider({ children, initialStage = 'input-evaluation', companyId = '' }: WizardProviderProps) {
  // Stage navigation
  const [currentStage, setCurrentStage] = useState<WizardStage>(initialStage)
  
  // Generate stable draft ID
  const { draftId: storedDraftId, setDraftId } = useWizardStore()
  const [wizardDraftId] = useState(() => {
    if (storedDraftId) return storedDraftId
    const newId = `draft-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    setDraftId(newId)
    return newId
  })
  
  // Messages
  const [messages, setMessages] = useState<Message[]>([])
  
  // Detected criteria
  const [detectedCriteria, setDetectedCriteria] = useState<DetectedCriteria>({
    cargo: null,
    gestorArea: null,
    responsabilidades: [],
    competenciasTecnicas: [],
    competenciasComportamentais: [],
    senioridadeIdiomas: null,
    modeloTrabalho: null,
    localizacao: null,
    tipoContrato: null,
    salario: null,
    departamento: null,
    isAffirmative: null,
    affirmativeCriteriaPrimary: null,
    affirmativeCriteriaSecondary: null,
    affirmativeDescription: null
  })
  
  // Basic info
  const [basicInfoFields, setBasicInfoFields] = useState<BasicInfoFields>({
    cargo: '',
    area: '',
    gestor: '',
    localidade: '',
    modeloTrabalho: '',
    tipoContrato: ''
  })
  
  // Technical skills
  const [technicalSkills, setTechnicalSkills] = useState<TechnicalSkill[]>([])
  
  // Behavioral competencies
  const [behavioralCompetencies, setBehavioralCompetencies] = useState<BehavioralCompetency[]>(INITIAL_BEHAVIORAL_COMPETENCIES)
  
  // Salary info
  const [salaryInfo, setSalaryInfo] = useState<SalaryInfo>({
    minSalary: '',
    maxSalary: '',
    minBonus: '',
    maxBonus: '',
    bonusCriteria: '',
    benefits: INITIAL_BENEFITS
  })
  const [salaryBenchmark, setSalaryBenchmark] = useState<SalaryBenchmark | null>(null)
  
  // WSI Questions
  const [wsiQuestions, setWsiQuestions] = useState<WSIQuestion[]>([])
  const [wsiCandidates, setWsiCandidates] = useState<WSIQuestionCandidate[]>([])
  const [isGeneratingWSI, setIsGeneratingWSI] = useState(false)
  const [companyDefaultQuestions, setCompanyDefaultQuestions] = useState<CompanyDefaultQuestion[]>([])
  const [wsiDroppedQuestions, setWsiDroppedQuestions] = useState<WSIDroppedQuestion[]>([])
  const [wsiFairnessWarning, setWsiFairnessWarning] = useState<WSIFairnessWarning | null>(null)

  // Bridge: hydrate FairnessGuard fields from backend `wizard_stage` payloads.
  // The WS handler (useChatSocket) and the unified-chat useWizardFlow hook both
  // dispatch `lia:wizard-stage-payload` window events whose `detail.data`
  // mirrors `ws_stage_payload.data`. For the `wsi_questions` stage we copy the
  // FairnessGuard drop list and warning summary into context so
  // `WSIQuestionsStage` can render its inline banner. Without this listener the
  // banner would stay hidden in real recruiter sessions even when the backend
  // sent the data over the wire.
  useEffect(() => {
    if (typeof window === 'undefined') return

    function handleStagePayload(event: Event) {
      const detail = (event as CustomEvent).detail as
        | {
            stage?: string
            data?: {
              dropped_questions?: WSIDroppedQuestion[] | null
              fairness_warning?: WSIFairnessWarning | null
            }
          }
        | undefined
      if (!detail || detail.stage !== 'wsi_questions') return
      const data = detail.data ?? {}
      setWsiDroppedQuestions(Array.isArray(data.dropped_questions) ? data.dropped_questions : [])
      setWsiFairnessWarning(data.fairness_warning ?? null)
    }

    window.addEventListener('lia:wizard-stage-payload', handleStagePayload as EventListener)
    return () => {
      window.removeEventListener('lia:wizard-stage-payload', handleStagePayload as EventListener)
    }
  }, [])
  
  // Calibration
  const [calibrationCandidates, setCalibrationCandidates] = useState<CalibrationCandidate[]>([])
  const [currentCalibrationIndex, setCurrentCalibrationIndex] = useState(0)
  const [approvedCandidates, setApprovedCandidates] = useState<string[]>([])
  const [rejectedCandidates, setRejectedCandidates] = useState<string[]>([])
  
  // Publishing
  const [publishingPlatforms, setPublishingPlatforms] = useState<PublishingPlatform[]>(INITIAL_PUBLISHING_PLATFORMS)
  
  // Job config
  const [jobConfig, setJobConfig] = useState<JobConfig>(() => {
    const now = new Date()
    return {
      urgencyLevel: 3,
      visibility: 'public',
      isConfidential: false,
      isAffirmative: false,
      deadline: new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      deadlineScreening: new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      deadlineShortlist: new Date(now.getTime() + 14 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      languages: []
    }
  })
  
  // Job description
  const [jobDescription, setJobDescription] = useState('')
  const [isGeneratingDescription, setIsGeneratingDescription] = useState(false)
  
  // Company config
  const [companyConfig, setCompanyConfig] = useState<CompanyConfig | null>(null)
  
  // Field origins
  const [fieldOrigins, setFieldOrigins] = useState<Record<string, { source: FieldOrigin; confidence: number }>>({})
  
  // Published job
  const [publishedJobId, setPublishedJobId] = useState<string | null>(null)
  
  // Company benefits from API
  const { benefits: companyBenefits, isLoading: isLoadingBenefits } = useCompanyBenefits()

  useEffect(() => {
    if (companyBenefits.length > 0) {
      setSalaryInfo(prev => {
        const isStillInitial = prev.benefits.length <= INITIAL_BENEFITS.length && 
          prev.benefits.every(b => INITIAL_BENEFITS.some(ib => ib.name === b.name))
        if (!isStillInitial) return prev
        
        const jobBenefits: JobBenefit[] = companyBenefits.map(cb => ({
          ...cb,
          enabled: cb.is_highlighted || cb.is_mandatory || false
        }))
        return { ...prev, benefits: jobBenefits }
      })
    }
  }, [companyBenefits])

  // UI states
  const [competenciesTab, setCompetenciesTab] = useState<'technical' | 'behavioral'>('technical')
  
  // Computed values
  const currentStageIndex = WIZARD_STAGES.findIndex(s => s.id === currentStage)
  
  // Navigation helpers
  const goToNextStage = useCallback(() => {
    const nextIndex = currentStageIndex + 1
    if (nextIndex < WIZARD_STAGES.length) {
      setCurrentStage(WIZARD_STAGES[nextIndex].id)
    }
  }, [currentStageIndex])
  
  const goToPreviousStage = useCallback(() => {
    const prevIndex = currentStageIndex - 1
    if (prevIndex >= 0) {
      setCurrentStage(WIZARD_STAGES[prevIndex].id)
    }
  }, [currentStageIndex])
  
  // Message helpers
  const addMessage = useCallback((message: Omit<Message, 'id' | 'timestamp'>) => {
    setMessages(prev => [...prev, {
      ...message,
      id: `msg-${Date.now()}`,
      timestamp: new Date()
    }])
  }, [])
  
  // Technical skill helpers
  const addTechnicalSkill = useCallback((skill: TechnicalSkill) => {
    setTechnicalSkills(prev => [...prev, skill])
  }, [])
  
  const removeTechnicalSkill = useCallback((id: string) => {
    setTechnicalSkills(prev => prev.filter(s => s.id !== id))
  }, [])
  
  const updateTechnicalSkill = useCallback((id: string, updates: Partial<TechnicalSkill>) => {
    setTechnicalSkills(prev => prev.map(s => s.id === id ? { ...s, ...updates } : s))
  }, [])
  
  // Behavioral competency helpers
  const toggleBehavioralCompetency = useCallback((id: string) => {
    setBehavioralCompetencies(prev => prev.map(c => 
      c.id === id ? { ...c, enabled: !c.enabled } : c
    ))
  }, [])
  
  const updateBehavioralCompetency = useCallback((id: string, updates: Partial<BehavioralCompetency>) => {
    setBehavioralCompetencies(prev => prev.map(c => c.id === id ? { ...c, ...updates } : c))
  }, [])
  
  // WSI helpers
  const toggleWSIQuestionSelection = useCallback((id: string) => {
    setWsiCandidates(prev => {
      const selectedCount = prev.filter(q => q.selected).length
      return prev.map(q => {
        if (q.id === id) {
          if (!q.selected && selectedCount >= 5) return q
          return { ...q, selected: !q.selected }
        }
        return q
      })
    })
  }, [])
  
  const deleteWSIQuestion = useCallback((id: string) => {
    setWsiCandidates(prev => prev.filter(q => q.id !== id))
  }, [])
  
  const updateWSIQuestionExpectedAnswer = useCallback((id: string, answer: unknown) => {
    setWsiCandidates(prev => prev.map(q => q.id === id ? { ...q, expectedAnswer: answer as WSIQuestion['expectedAnswer'] } : q))
  }, [])
  
  // Platform helpers
  const togglePlatform = useCallback((id: string) => {
    setPublishingPlatforms(prev => prev.map(p => 
      p.id === id ? { ...p, enabled: !p.enabled } : p
    ))
  }, [])
  
  // Can advance check
  const canAdvance = (() => {
    switch (currentStage) {
      case 'input-evaluation':
        return detectedCriteria.cargo !== null
      case 'job-description':
        return basicInfoFields.cargo.length > 0
      case 'competencies':
        return technicalSkills.length >= 3 && behavioralCompetencies.filter(c => c.enabled).length >= 3
      case 'salary':
        return true
      case 'wsi-questions':
        return wsiCandidates.filter(q => q.selected).length >= 3
      case 'review-publish':
        return true
      case 'search-calibration':
        return calibrationCandidates.length > 0
      default:
        return true
    }
  })()
  
  // Auto-advance check
  const shouldAutoAdvance = useCallback((confidence: number) => {
    const threshold = AUTO_ADVANCE_CONFIDENCE_THRESHOLDS[currentStage]
    return confidence >= threshold && currentStage !== 'review-publish' && currentStage !== 'search-calibration'
  }, [currentStage])
  
  // Reset wizard
  const resetWizard = useCallback(() => {
    setCurrentStage('input-evaluation')
    setMessages([])
    setDetectedCriteria({
      cargo: null,
      gestorArea: null,
      responsabilidades: [],
      competenciasTecnicas: [],
      competenciasComportamentais: [],
      senioridadeIdiomas: null,
      modeloTrabalho: null,
      localizacao: null,
      tipoContrato: null,
      salario: null,
      departamento: null,
      isAffirmative: null,
      affirmativeCriteriaPrimary: null,
      affirmativeCriteriaSecondary: null,
      affirmativeDescription: null
    })
    setBasicInfoFields({ cargo: '', area: '', gestor: '', localidade: '', modeloTrabalho: '', tipoContrato: '' })
    setTechnicalSkills([])
    setBehavioralCompetencies(INITIAL_BEHAVIORAL_COMPETENCIES)
    setSalaryInfo({ minSalary: '', maxSalary: '', minBonus: '', maxBonus: '', bonusCriteria: '', benefits: INITIAL_BENEFITS })
    setWsiQuestions([])
    setWsiCandidates([])
    setCalibrationCandidates([])
    setJobDescription('')
    setPublishedJobId(null)
    setDraftId(null)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])
  
  const value: WizardContextValue = {
    currentStage,
    setCurrentStage,
    goToNextStage,
    goToPreviousStage,
    canAdvance,
    currentStageIndex,
    messages,
    setMessages,
    addMessage,
    detectedCriteria,
    setDetectedCriteria,
    basicInfoFields,
    setBasicInfoFields,
    technicalSkills,
    setTechnicalSkills,
    addTechnicalSkill,
    removeTechnicalSkill,
    updateTechnicalSkill,
    behavioralCompetencies,
    setBehavioralCompetencies,
    toggleBehavioralCompetency,
    updateBehavioralCompetency,
    salaryInfo,
    setSalaryInfo,
    salaryBenchmark,
    setSalaryBenchmark,
    wsiQuestions,
    setWsiQuestions,
    wsiCandidates,
    setWsiCandidates,
    toggleWSIQuestionSelection,
    deleteWSIQuestion,
    updateWSIQuestionExpectedAnswer,
    isGeneratingWSI,
    setIsGeneratingWSI,
    companyDefaultQuestions,
    setCompanyDefaultQuestions,
    wsiDroppedQuestions,
    setWsiDroppedQuestions,
    wsiFairnessWarning,
    setWsiFairnessWarning,
    calibrationCandidates,
    setCalibrationCandidates,
    currentCalibrationIndex,
    setCurrentCalibrationIndex,
    approvedCandidates,
    setApprovedCandidates,
    rejectedCandidates,
    setRejectedCandidates,
    publishingPlatforms,
    setPublishingPlatforms,
    togglePlatform,
    jobConfig,
    setJobConfig,
    jobDescription,
    setJobDescription,
    isGeneratingDescription,
    setIsGeneratingDescription,
    companyConfig,
    setCompanyConfig,
    fieldOrigins,
    setFieldOrigins,
    wizardDraftId,
    publishedJobId,
    setPublishedJobId,
    competenciesTab,
    setCompetenciesTab,
    shouldAutoAdvance,
    resetWizard
  }
  
  return (
    <WizardContext.Provider value={value}>
      {children}
    </WizardContext.Provider>
  )
}

export function useWizardContext() {
  const context = useContext(WizardContext)
  if (!context) {
    throw new Error('useWizardContext must be used within a WizardProvider')
  }
  return context
}

export { WizardContext }
