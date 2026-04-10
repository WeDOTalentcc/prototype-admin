"use client"

import { useState, useEffect, useCallback, useRef } from 'react'
import { useWizardStore } from '@/stores/wizard-store'

interface BasicInfoFields {
  jobTitle?: string
  seniority?: string
  department?: string
  manager?: string
  area?: string
  locality?: string
  workModel?: string
  employmentType?: string
  responsibilities?: string[]
}

interface TechnicalSkill {
  id: string
  name: string
  level: 'Básico' | 'Intermediário' | 'Avançado'
  required: boolean
  category: 'language' | 'framework' | 'database' | 'tool' | 'general'
  weight: number
  weightJustification?: string
  isWeightInferred?: boolean
}

interface BehavioralCompetency {
  id: string
  name: string
  weight: number
  justification: string
  enabled: boolean
  weightJustification?: string
  isWeightInferred?: boolean
}

interface Benefit {
  id: string
  name: string
  value?: string
  enabled: boolean
}

interface SalaryInfo {
  minSalary: string
  maxSalary: string
  minBonus: string
  maxBonus: string
  bonusCriteria: string
  benefits: Benefit[]
}

interface WSIQuestionCandidate {
  id: string
  question: string
  type: 'open' | 'yes-no' | 'numeric' | 'multiple-choice'
  required: boolean
  options?: string[]
  expectedAnswer?: string | number | boolean
  correctOptionIndex?: number
  selected: boolean
  batch: number
  isWSI?: boolean
  competency?: string
  framework?: string
  category?: 'technical' | 'behavioral' | 'autodeclaracao_contexto' | 'micro_case' | 'situacional' | 'fit' | 'autodeclaracao'
}

interface WizardDraftData {
  jobDraftId?: string
  basicInfoFields: BasicInfoFields
  salaryInfo: SalaryInfo
  technicalSkills: TechnicalSkill[]
  behavioralCompetencies: BehavioralCompetency[]
  jobDescription?: string
  wsiCandidates: WSIQuestionCandidate[]
  currentStage: string
  lastSavedAt: string
}

interface UseWizardAutoSaveOptions {
  enabled?: boolean
  saveInterval?: number
  jobDraftId?: string
  skipUntilRestored?: boolean
}

interface UseWizardAutoSaveReturn {
  isSaving: boolean
  lastSavedAt: Date | null
  hasPendingChanges: boolean
  saveNow: () => Promise<void>
  loadDraft: (draftId: string) => Promise<void>
  clearDraft: () => void
  loadedDraft: Partial<WizardDraftData> | null
  hasRestoredDraft: boolean
  hasAttemptedRestore: boolean
  getLastSavedText: () => string
}

const BACKEND_DRAFT_ENDPOINT = '/api/backend-proxy/job-drafts'

export function useWizardAutoSave(
  draftData: Partial<WizardDraftData>,
  options: UseWizardAutoSaveOptions = {}
): UseWizardAutoSaveReturn {
  const {
    enabled = true,
    saveInterval = 30000,
    jobDraftId,
    skipUntilRestored = false
  } = options

  const wizardStore = useWizardStore()

  const [isSaving, setIsSaving] = useState(false)
  const [lastSavedAt, setLastSavedAt] = useState<Date | null>(null)
  const [hasPendingChanges, setHasPendingChanges] = useState(false)
  const [draftState, setDraftState] = useState<Partial<WizardDraftData>>(draftData)
  const [loadedDraft, setLoadedDraft] = useState<Partial<WizardDraftData> | null>(null)
  const [hasRestoredDraft, setHasRestoredDraft] = useState(false)
  const [hasAttemptedRestore, setHasAttemptedRestore] = useState(false)

  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null)
  const autoSaveIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const lastDraftDataRef = useRef<Partial<WizardDraftData>>(draftData)
  const lastDraftDataJsonRef = useRef<string>(JSON.stringify(draftData))

  const saveToStore = useCallback((data: Partial<WizardDraftData>) => {
    try {
      const dataWithTimestamp = {
        ...data,
        lastSavedAt: new Date().toISOString(),
        jobDraftId: jobDraftId || data.jobDraftId
      }
      wizardStore.setDraft(dataWithTimestamp as Parameters<typeof wizardStore.setDraft>[0])
    } catch {
    }
  }, [jobDraftId, wizardStore])

  const saveToBackend = useCallback(async (data: Partial<WizardDraftData>) => {
    try {
      const draftId = jobDraftId || data.jobDraftId || 'temp-' + Date.now()
      
      const response = await fetch(`${BACKEND_DRAFT_ENDPOINT}/${draftId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          id: draftId,
          data: {
            basicInfoFields: data.basicInfoFields || {},
            salaryInfo: data.salaryInfo || {},
            technicalSkills: data.technicalSkills || [],
            behavioralCompetencies: data.behavioralCompetencies || [],
            jobDescription: data.jobDescription || '',
            wsiCandidates: data.wsiCandidates || [],
            currentStage: data.currentStage || 'description'
          },
          savedAt: new Date().toISOString()
        })
      })

      if (!response.ok) {
        return false
      }

      return true
    } catch {
      return false
    }
  }, [jobDraftId])

  const performSave = useCallback(async () => {
    if (!enabled || !hasPendingChanges) {
      return
    }
    
    if (skipUntilRestored) {
      return
    }

    setIsSaving(true)

    try {
      saveToStore(draftState)

      await saveToBackend(draftState)

      lastDraftDataRef.current = JSON.parse(JSON.stringify(draftState))
      setLastSavedAt(new Date())
      setHasPendingChanges(false)
    } catch {
    } finally {
      setIsSaving(false)
    }
  }, [enabled, hasPendingChanges, draftState, saveToStore, saveToBackend, skipUntilRestored])

  const saveNow = useCallback(async () => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current)
    }

    await performSave()
  }, [performSave])

  const loadDraft = useCallback(async (draftId: string) => {
    try {
      const response = await fetch(`${BACKEND_DRAFT_ENDPOINT}/${draftId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        const backendData = await response.json()
        const draft = backendData.data || backendData
        setDraftState(draft)
        setLoadedDraft(draft)
        setHasRestoredDraft(true)
        lastDraftDataRef.current = JSON.parse(JSON.stringify(draft))
        setLastSavedAt(backendData.savedAt ? new Date(backendData.savedAt) : null)
        setHasPendingChanges(false)
        return
      }
    } catch {
    }

    try {
      const storedDraft = wizardStore.draft
      if (storedDraft) {
        const parsed = storedDraft as Partial<WizardDraftData>
        setDraftState(parsed)
        setLoadedDraft(parsed)
        setHasRestoredDraft(true)
        lastDraftDataRef.current = JSON.parse(JSON.stringify(parsed))
        const savedAt = (parsed as Record<string, unknown>).lastSavedAt
        setLastSavedAt(savedAt ? new Date(savedAt as string) : null)
        setHasPendingChanges(false)
      }
    } catch {
    }
  }, [wizardStore])

  useEffect(() => {
    const attemptRestore = async () => {
      if (jobDraftId) {
        await loadDraft(jobDraftId)
      } else {
        try {
          const storedDraft = wizardStore.draft
          if (storedDraft) {
            const parsed = storedDraft as Partial<WizardDraftData>
            setDraftState(parsed)
            setLoadedDraft(parsed)
            setHasRestoredDraft(true)
            lastDraftDataRef.current = JSON.parse(JSON.stringify(parsed))
            const savedAt = (parsed as Record<string, unknown>).lastSavedAt
            setLastSavedAt(savedAt ? new Date(savedAt as string) : null)
          }
        } catch {
        }
      }
      setHasAttemptedRestore(true)
    }
    
    attemptRestore()
  }, [jobDraftId, loadDraft, wizardStore])

  useEffect(() => {
    if (skipUntilRestored) {
      return
    }
    
    const currentDataStr = JSON.stringify(draftData)
    
    if (currentDataStr !== lastDraftDataJsonRef.current) {
      lastDraftDataJsonRef.current = currentDataStr
      setDraftState(draftData)
      setHasPendingChanges(true)
    }
  }, [draftData, skipUntilRestored])

  useEffect(() => {
    if (!enabled) {
      return
    }

    if (autoSaveIntervalRef.current) {
      clearInterval(autoSaveIntervalRef.current)
    }

    autoSaveIntervalRef.current = setInterval(() => {
      if (hasPendingChanges) {
        performSave()
      }
    }, saveInterval)

    const intervalToCleanup = autoSaveIntervalRef
    return () => {
      if (intervalToCleanup.current) {
        clearInterval(intervalToCleanup.current)
      }
    }
  }, [enabled, hasPendingChanges, saveInterval, performSave])

  useEffect(() => {
    const debounceTimer = debounceTimerRef
    const autoSaveInterval = autoSaveIntervalRef
    return () => {
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current)
      }
      if (autoSaveInterval.current) {
        clearInterval(autoSaveInterval.current)
      }
    }
  }, [])

  const clearDraft = useCallback(() => {
    try {
      wizardStore.clearDraft()
      setDraftState({})
      setLoadedDraft(null)
      setHasRestoredDraft(false)
      setLastSavedAt(null)
      setHasPendingChanges(false)
      lastDraftDataRef.current = {}

      if (jobDraftId) {
        fetch(`${BACKEND_DRAFT_ENDPOINT}/${jobDraftId}`, {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json'
          }
        }).catch((err) => { console.warn('[useWizardAutoSave] draft DELETE fire-and-forget failed', err) })
      }
    } catch {
    }
  }, [jobDraftId, wizardStore])

  const getLastSavedText = useCallback((): string => {
    if (!lastSavedAt) return ''
    
    const diff = Date.now() - lastSavedAt.getTime()
    const minutes = Math.floor(diff / 60000)
    
    if (minutes < 1) return 'Salvo agora'
    if (minutes === 1) return 'Salvo há 1 minuto'
    if (minutes < 60) return `Salvo há ${minutes} minutos`
    
    const hours = Math.floor(minutes / 60)
    if (hours === 1) return 'Salvo há 1 hora'
    if (hours < 24) return `Salvo há ${hours} horas`
    
    const days = Math.floor(hours / 24)
    if (days === 1) return 'Salvo há 1 dia'
    return `Salvo há ${days} dias`
  }, [lastSavedAt])

  return {
    isSaving,
    lastSavedAt,
    hasPendingChanges,
    saveNow,
    loadDraft,
    clearDraft,
    loadedDraft,
    hasRestoredDraft,
    hasAttemptedRestore,
    getLastSavedText
  }
}

export default useWizardAutoSave
