'use client'

import { useState, useCallback, useMemo } from 'react'
import { useWizardStore } from '@/stores/wizard-store'
import {
  type WizardContextState,
  type WizardContextActions,
  type ExpandedChatContextValue,
  type TechnicalSkill,
  type BehavioralCompetency,
  type SalaryInfo,
  type WSIQuestion,
  type DetectedCriteria,
  type BasicInfoFields,
  type CatalogMaturity,
  type OrchestratorFieldUpdates,
  INITIAL_DETECTED_CRITERIA,
  INITIAL_BASIC_INFO_FIELDS,
  INITIAL_SALARY_INFO,
  DEFAULT_BEHAVIORAL_COMPETENCIES,
} from '../ExpandedChatContext'
import type { FastTrackJobData } from '@/hooks/useFastTrack'
import { type WizardStage, WIZARD_STAGES } from '../config'
import { useWSIQualityGates } from './useWSIQualityGates'

function generateDraftId(): string {
  return `draft-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}

function getOrCreateDraftId(existingId: string | null, setDraftId: (id: string | null) => void): string {
  if (existingId) return existingId
  const newId = generateDraftId()
  setDraftId(newId)
  return newId
}

export interface UseWizardStateOptions {
  initialStage?: WizardStage
  onStageChange?: (stage: WizardStage, index: number) => void
  onPendingChanges?: (hasPendingChanges: boolean) => void
  onFieldChange?: (field: string, oldValue: unknown, newValue: unknown, source?: 'panel' | 'chat' | 'orchestrator') => void
}

export type UseWizardStateReturn = ExpandedChatContextValue

export function useWizardState(options: UseWizardStateOptions = {}): UseWizardStateReturn {
  const { initialStage = 'input-evaluation', onStageChange, onPendingChanges, onFieldChange } = options

  const [currentStage, setCurrentStageInternal] = useState<WizardStage>(initialStage)
  const { draftId: storedDraftId, setDraftId } = useWizardStore()
  const [wizardDraftId] = useState(() => getOrCreateDraftId(storedDraftId, setDraftId))
  const [basicInfoFields, setBasicInfoFieldsState] = useState<BasicInfoFields>(INITIAL_BASIC_INFO_FIELDS)
  const [technicalSkills, setTechnicalSkillsState] = useState<TechnicalSkill[]>([])
  const [behavioralCompetencies, setBehavioralCompetenciesState] = useState<BehavioralCompetency[]>(DEFAULT_BEHAVIORAL_COMPETENCIES)
  const [salaryInfo, setSalaryInfoState] = useState<SalaryInfo>(INITIAL_SALARY_INFO)
  const [wsiQuestions, setWSIQuestionsState] = useState<WSIQuestion[]>([])
  const [detectedCriteria, setDetectedCriteriaState] = useState<DetectedCriteria>(INITIAL_DETECTED_CRITERIA)
  const [generatedJobDescription, setGeneratedJobDescriptionState] = useState<string>('')
  const [hasRestoredDraft, setHasRestoredDraftState] = useState(false)
  const [hasPendingChanges, setHasPendingChangesState] = useState(false)
  const [catalogMaturity, setCatalogMaturityState] = useState<CatalogMaturity>('minimal')
  const [isLoading, setIsLoadingState] = useState(false)
  const [fastTrackSourceJobId, setFastTrackSourceJobId] = useState<string | null>(null)

  const currentStageIndex = useMemo(() => {
    return WIZARD_STAGES.findIndex(s => s.id === currentStage)
  }, [currentStage])

  const markPendingChanges = useCallback(() => {
    if (!hasPendingChanges) {
      setHasPendingChangesState(true)
      onPendingChanges?.(true)
    }
  }, [hasPendingChanges, onPendingChanges])

  const setCurrentStage = useCallback((stage: WizardStage) => {
    setCurrentStageInternal(stage)
    const index = WIZARD_STAGES.findIndex(s => s.id === stage)
    onStageChange?.(stage, index)
  }, [onStageChange])

  const advanceStage = useCallback(() => {
    const nextIndex = currentStageIndex + 1
    if (nextIndex < WIZARD_STAGES.length) {
      const nextStage = WIZARD_STAGES[nextIndex].id as WizardStage
      setCurrentStage(nextStage)
    }
  }, [currentStageIndex, setCurrentStage])

  const goBackStage = useCallback(() => {
    const prevIndex = currentStageIndex - 1
    if (prevIndex >= 0) {
      const prevStage = WIZARD_STAGES[prevIndex].id as WizardStage
      setCurrentStage(prevStage)
    }
  }, [currentStageIndex, setCurrentStage])

  const updateBasicInfoField = useCallback((field: keyof BasicInfoFields, value: string) => {
    setBasicInfoFieldsState(prev => {
      const oldValue = prev[field]
      onFieldChange?.(field, oldValue, value, 'panel')
      return { ...prev, [field]: value }
    })
    markPendingChanges()
  }, [markPendingChanges, onFieldChange])

  const updateBasicInfoFields = useCallback((fields: Partial<BasicInfoFields>) => {
    setBasicInfoFieldsState(prev => {
      Object.entries(fields).forEach(([key, value]) => {
        const oldValue = prev[key as keyof BasicInfoFields]
        onFieldChange?.(key, oldValue, value, 'panel')
      })
      return { ...prev, ...fields }
    })
    markPendingChanges()
  }, [markPendingChanges, onFieldChange])

  const updateSalaryInfo = useCallback((info: Partial<SalaryInfo>) => {
    setSalaryInfoState(prev => {
      Object.entries(info).forEach(([key, value]) => {
        if (key !== 'benefits') {
          const oldValue = prev[key as keyof SalaryInfo]
          onFieldChange?.(key, oldValue, value, 'panel')
        }
      })
      return { ...prev, ...info }
    })
    markPendingChanges()
  }, [markPendingChanges, onFieldChange])

  const addTechnicalSkill = useCallback((skill: TechnicalSkill) => {
    setTechnicalSkillsState(prev => [...prev, skill])
    onFieldChange?.('technicalSkill', null, skill, 'panel')
    markPendingChanges()
  }, [markPendingChanges, onFieldChange])

  const removeTechnicalSkill = useCallback((skillId: string) => {
    setTechnicalSkillsState(prev => {
      const skill = prev.find(s => s.id === skillId)
      if (skill) {
        onFieldChange?.('technicalSkill', skill, null, 'panel')
      }
      return prev.filter(s => s.id !== skillId)
    })
    markPendingChanges()
  }, [markPendingChanges, onFieldChange])

  const updateTechnicalSkill = useCallback((skillId: string, updates: Partial<TechnicalSkill>) => {
    setTechnicalSkillsState(prev => {
      const skill = prev.find(s => s.id === skillId)
      if (skill) {
        const newSkill = { ...skill, ...updates }
        onFieldChange?.('technicalSkill', skill, newSkill, 'panel')
      }
      return prev.map(s => s.id === skillId ? { ...s, ...updates } : s)
    })
    markPendingChanges()
  }, [markPendingChanges, onFieldChange])

  const setTechnicalSkills = useCallback((skills: TechnicalSkill[]) => {
    setTechnicalSkillsState(skills)
    markPendingChanges()
  }, [markPendingChanges])

  const addBehavioralCompetency = useCallback((competency: BehavioralCompetency) => {
    setBehavioralCompetenciesState(prev => [...prev, competency])
    onFieldChange?.('behavioralCompetency', null, competency, 'panel')
    markPendingChanges()
  }, [markPendingChanges, onFieldChange])

  const removeBehavioralCompetency = useCallback((competencyId: string) => {
    setBehavioralCompetenciesState(prev => {
      const competency = prev.find(c => c.id === competencyId)
      if (competency) {
        onFieldChange?.('behavioralCompetency', competency, null, 'panel')
      }
      return prev.filter(c => c.id !== competencyId)
    })
    markPendingChanges()
  }, [markPendingChanges, onFieldChange])

  const updateBehavioralCompetency = useCallback((competencyId: string, updates: Partial<BehavioralCompetency>) => {
    setBehavioralCompetenciesState(prev => {
      const competency = prev.find(c => c.id === competencyId)
      if (competency) {
        const newCompetency = { ...competency, ...updates }
        onFieldChange?.('behavioralCompetency', competency, newCompetency, 'panel')
      }
      return prev.map(c => c.id === competencyId ? { ...c, ...updates } : c)
    })
    markPendingChanges()
  }, [markPendingChanges, onFieldChange])

  const toggleBehavioralCompetency = useCallback((competencyId: string) => {
    setBehavioralCompetenciesState(prev => {
      const competency = prev.find(c => c.id === competencyId)
      if (competency) {
        onFieldChange?.('behavioralCompetency', competency, { ...competency, enabled: !competency.enabled }, 'panel')
      }
      return prev.map(c => c.id === competencyId ? { ...c, enabled: !c.enabled } : c)
    })
    markPendingChanges()
  }, [markPendingChanges, onFieldChange])

  const setBehavioralCompetencies = useCallback((competencies: BehavioralCompetency[]) => {
    setBehavioralCompetenciesState(competencies)
    markPendingChanges()
  }, [markPendingChanges])

  const addWSIQuestion = useCallback((question: WSIQuestion) => {
    setWSIQuestionsState(prev => [...prev, question])
    markPendingChanges()
  }, [markPendingChanges])

  const removeWSIQuestion = useCallback((questionId: string) => {
    setWSIQuestionsState(prev => prev.filter(q => q.id !== questionId))
    markPendingChanges()
  }, [markPendingChanges])

  const updateWSIQuestion = useCallback((questionId: string, updates: Partial<WSIQuestion>) => {
    setWSIQuestionsState(prev =>
      prev.map(q => q.id === questionId ? { ...q, ...updates } : q)
    )
    markPendingChanges()
  }, [markPendingChanges])

  const setWSIQuestions = useCallback((questions: WSIQuestion[]) => {
    setWSIQuestionsState(questions)
    markPendingChanges()
  }, [markPendingChanges])

  const setGeneratedJobDescription = useCallback((description: string) => {
    setGeneratedJobDescriptionState(description)
    markPendingChanges()
  }, [markPendingChanges])

  const updateDetectedCriteria = useCallback((criteria: Partial<DetectedCriteria>) => {
    setDetectedCriteriaState(prev => ({ ...prev, ...criteria }))
    markPendingChanges()
  }, [markPendingChanges])

  const setDetectedCriteria = useCallback((criteria: DetectedCriteria) => {
    setDetectedCriteriaState(criteria)
    markPendingChanges()
  }, [markPendingChanges])

  const resetWizard = useCallback(() => {
    setCurrentStageInternal('input-evaluation')
    setBasicInfoFieldsState(INITIAL_BASIC_INFO_FIELDS)
    setTechnicalSkillsState([])
    setBehavioralCompetenciesState(DEFAULT_BEHAVIORAL_COMPETENCIES)
    setSalaryInfoState(INITIAL_SALARY_INFO)
    setWSIQuestionsState([])
    setDetectedCriteriaState(INITIAL_DETECTED_CRITERIA)
    setGeneratedJobDescriptionState('')
    setHasRestoredDraftState(false)
    setHasPendingChangesState(false)
    setCatalogMaturityState('minimal')
    setFastTrackSourceJobId(null)
    setDraftId(null)
  }, [])

  const setHasPendingChanges = useCallback((value: boolean) => {
    setHasPendingChangesState(value)
    onPendingChanges?.(value)
  }, [onPendingChanges])

  const setHasRestoredDraft = useCallback((value: boolean) => {
    setHasRestoredDraftState(value)
  }, [])

  const setCatalogMaturity = useCallback((maturity: CatalogMaturity) => {
    setCatalogMaturityState(maturity)
  }, [])

  const setIsLoading = useCallback((value: boolean) => {
    setIsLoadingState(value)
  }, [])

  const applyOrchestratorUpdates = useCallback((updates: OrchestratorFieldUpdates) => {
    if (updates.salaryInfo && Object.keys(updates.salaryInfo).length > 0) {
      setSalaryInfoState(prev => ({ ...prev, ...updates.salaryInfo }))
    }
    
    if (updates.basicInfoFields && Object.keys(updates.basicInfoFields).length > 0) {
      setBasicInfoFieldsState(prev => ({ ...prev, ...updates.basicInfoFields }))
    }
    
    if (updates.detectedCriteria && Object.keys(updates.detectedCriteria).length > 0) {
      setDetectedCriteriaState(prev => ({ ...prev, ...updates.detectedCriteria }))
    }
    
    if (updates.technicalSkills && updates.technicalSkills.length > 0) {
      setTechnicalSkillsState(prev => {
        const existingNames = new Set(prev.map(s => s.name.toLowerCase()))
        const newSkills = updates.technicalSkills!.filter(
          s => !existingNames.has(s.name.toLowerCase())
        )
        return [...prev, ...newSkills]
      })
    }
    
    if (updates.behavioralCompetencies && updates.behavioralCompetencies.length > 0) {
      setBehavioralCompetenciesState(prev => {
        const existingNames = new Set(prev.map(c => c.name.toLowerCase()))
        const newComps = updates.behavioralCompetencies!.filter(
          c => !existingNames.has(c.name.toLowerCase())
        )
        return [...prev, ...newComps]
      })
    }
    
    markPendingChanges()
  }, [markPendingChanges])
  
  const applyFastTrackData = useCallback((data: FastTrackJobData) => {
    if (data.sourceJobId) {
      setFastTrackSourceJobId(data.sourceJobId)
    }
    
    if (data.basicInfo) {
      setBasicInfoFieldsState(prev => ({ ...prev, ...data.basicInfo }))
    }
    
    if (data.technicalSkills && data.technicalSkills.length > 0) {
      setTechnicalSkillsState(data.technicalSkills)
    }
    
    if (data.behavioralCompetencies && data.behavioralCompetencies.length > 0) {
      setBehavioralCompetenciesState(data.behavioralCompetencies)
    }
    
    if (data.salaryInfo) {
      setSalaryInfoState(prev => ({ ...prev, ...data.salaryInfo }))
    }
    
    if (data.wsiQuestions && data.wsiQuestions.length > 0) {
      setWSIQuestionsState(data.wsiQuestions)
    }
    
    if (data.detectedCriteria) {
      setDetectedCriteriaState(prev => ({ ...prev, ...data.detectedCriteria }))
    }
    
    if (data.generatedDescription) {
      setGeneratedJobDescriptionState(data.generatedDescription)
    }
    
    markPendingChanges()
  }, [markPendingChanges])
  
  const skipToReviewStage = useCallback(() => {
    const reviewStage = WIZARD_STAGES.find(s => s.id === 'review-publish')
    if (reviewStage) {
      setCurrentStageInternal('review-publish')
      const index = WIZARD_STAGES.findIndex(s => s.id === 'review-publish')
      onStageChange?.('review-publish', index)
    }
  }, [onStageChange])

  const wsiQualityGates = useWSIQualityGates({
    technicalSkills,
    behavioralCompetencies,
    detectedCriteria,
    generatedJobDescription,
    minScoreToAdvance: 70,
  })

  const wsiQualityScore = wsiQualityGates.score
  const wsiMissingFields = wsiQualityGates.missingFields
  
  const canAdvanceStage = useCallback((): boolean => {
    return wsiQualityGates.canAdvance
  }, [wsiQualityGates.canAdvance])

  const state: WizardContextState = {
    currentStage,
    currentStageIndex,
    wizardDraftId,
    basicInfoFields,
    technicalSkills,
    behavioralCompetencies,
    salaryInfo,
    wsiQuestions,
    detectedCriteria,
    generatedJobDescription,
    hasRestoredDraft,
    hasPendingChanges,
    catalogMaturity,
    isLoading,
    wsiQualityScore,
    wsiMissingFields,
    fastTrackSourceJobId,
  }

  const actions: WizardContextActions = {
    setCurrentStage,
    advanceStage,
    goBackStage,
    updateBasicInfoField,
    updateBasicInfoFields,
    updateSalaryInfo,
    addTechnicalSkill,
    removeTechnicalSkill,
    updateTechnicalSkill,
    setTechnicalSkills,
    addBehavioralCompetency,
    removeBehavioralCompetency,
    updateBehavioralCompetency,
    toggleBehavioralCompetency,
    setBehavioralCompetencies,
    addWSIQuestion,
    removeWSIQuestion,
    updateWSIQuestion,
    setWSIQuestions,
    setGeneratedJobDescription,
    updateDetectedCriteria,
    setDetectedCriteria,
    resetWizard,
    setHasPendingChanges,
    setHasRestoredDraft,
    setCatalogMaturity,
    setIsLoading,
    canAdvanceStage,
    applyOrchestratorUpdates,
    applyFastTrackData,
    skipToReviewStage,
  }

  return { ...state, ...actions }
}
