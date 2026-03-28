"use client"

import { useState, useEffect, useCallback, useRef } from 'react'

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
  category: 'language' | 'framework' | 'database' | 'tool'
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

const LOCAL_STORAGE_KEY = 'wizard_draft'
const DRAFT_ID_KEY = 'wizard_draft_id'
const BACKEND_DRAFT_ENDPOINT = '/api/backend-proxy/job-drafts'

export function useWizardAutoSave(
  draftData: Partial<WizardDraftData>,
  options: UseWizardAutoSaveOptions = {}
): UseWizardAutoSaveReturn {
  const {
    enabled = true,
    saveInterval = 30000, // 30 seconds
    jobDraftId,
    skipUntilRestored = false
  } = options

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

  // Check if data has changed
  const hasDataChanged = useCallback((): boolean => {
    const current = JSON.stringify(draftState)
    const previous = JSON.stringify(lastDraftDataRef.current)
    return current !== previous
  }, [draftState])

  // Save to local storage
  const saveToLocalStorage = useCallback((data: Partial<WizardDraftData>) => {
    try {
      const dataWithTimestamp = {
        ...data,
        lastSavedAt: new Date().toISOString(),
        jobDraftId: jobDraftId || data.jobDraftId
      }
      localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(dataWithTimestamp))
    } catch (error) {
      console.error('Failed to save draft to localStorage:', error)
    }
  }, [jobDraftId])

  // Save to backend
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
        // Only log warning, don't throw - backend saves are non-critical
        console.warn(`Backend draft save failed: ${response.status}`)
        return false
      }

      return true
    } catch (error) {
      // Silently handle backend errors - localStorage is the fallback
      console.warn('Backend draft save error:', error)
      return false
    }
  }, [jobDraftId])

  // Main save function
  const performSave = useCallback(async () => {
    if (!enabled || !hasPendingChanges) {
      return
    }
    
    // Skip save if waiting for restoration to be applied (controlled by component)
    if (skipUntilRestored) {
      return
    }

    setIsSaving(true)

    try {
      // Save to localStorage first (always works)
      saveToLocalStorage(draftState)

      // Save to backend (non-critical)
      await saveToBackend(draftState)

      lastDraftDataRef.current = JSON.parse(JSON.stringify(draftState))
      setLastSavedAt(new Date())
      setHasPendingChanges(false)
    } catch (error) {
      console.error('Error during save:', error)
      // Keep hasPendingChanges true so user knows something wasn't saved
    } finally {
      setIsSaving(false)
    }
  }, [enabled, hasPendingChanges, draftState, saveToLocalStorage, saveToBackend])

  // Debounced save function
  const saveNow = useCallback(async () => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current)
    }

    await performSave()
  }, [performSave])

  // Load draft from localStorage or backend
  const loadDraft = useCallback(async (draftId: string) => {
    try {
      // Try loading from backend first
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
    } catch (error) {
      console.warn('Failed to load draft from backend:', error)
    }

    // Fallback to localStorage
    try {
      const localData = localStorage.getItem(LOCAL_STORAGE_KEY)
      if (localData) {
        const parsed = JSON.parse(localData)
        setDraftState(parsed)
        setLoadedDraft(parsed)
        setHasRestoredDraft(true)
        lastDraftDataRef.current = JSON.parse(JSON.stringify(parsed))
        setLastSavedAt(parsed.lastSavedAt ? new Date(parsed.lastSavedAt) : null)
        setHasPendingChanges(false)
      }
    } catch (error) {
      console.warn('Failed to load draft from localStorage:', error)
    }
  }, [])

  // Load initial draft if available
  useEffect(() => {
    const attemptRestore = async () => {
      if (jobDraftId) {
        await loadDraft(jobDraftId)
      } else {
        // Try loading from localStorage
        try {
          const localData = localStorage.getItem(LOCAL_STORAGE_KEY)
          if (localData) {
            const parsed = JSON.parse(localData)
            setDraftState(parsed)
            setLoadedDraft(parsed)
            setHasRestoredDraft(true)
            lastDraftDataRef.current = JSON.parse(JSON.stringify(parsed))
            setLastSavedAt(parsed.lastSavedAt ? new Date(parsed.lastSavedAt) : null)
          }
        } catch (error) {
          console.warn('Failed to load initial draft:', error)
        }
      }
      // Mark restore attempt as complete (regardless of success or failure)
      setHasAttemptedRestore(true)
    }
    
    attemptRestore()
  }, [jobDraftId, loadDraft])

  // Update draft state and mark as pending
  useEffect(() => {
    // Don't update state until restoration is complete (controlled by component)
    if (skipUntilRestored) {
      return
    }
    
    // Compare by content using ref to avoid infinite loops from object reference changes
    const currentDataStr = JSON.stringify(draftData)
    
    // Only update if the content actually changed
    if (currentDataStr !== lastDraftDataJsonRef.current) {
      lastDraftDataJsonRef.current = currentDataStr
      setDraftState(draftData)
      setHasPendingChanges(true)
    }
  }, [draftData, skipUntilRestored])

  // Setup auto-save interval
  useEffect(() => {
    if (!enabled) {
      return
    }

    // Clear any existing interval
    if (autoSaveIntervalRef.current) {
      clearInterval(autoSaveIntervalRef.current)
    }

    // Setup new interval
    autoSaveIntervalRef.current = setInterval(() => {
      if (hasPendingChanges) {
        performSave()
      }
    }, saveInterval)

    return () => {
      if (autoSaveIntervalRef.current) {
        clearInterval(autoSaveIntervalRef.current)
      }
    }
  }, [enabled, hasPendingChanges, saveInterval, performSave])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current)
      }
      if (autoSaveIntervalRef.current) {
        clearInterval(autoSaveIntervalRef.current)
      }
    }
  }, [])

  // Clear draft
  const clearDraft = useCallback(() => {
    try {
      localStorage.removeItem(LOCAL_STORAGE_KEY)
      localStorage.removeItem(DRAFT_ID_KEY)
      setDraftState({})
      setLoadedDraft(null)
      setHasRestoredDraft(false)
      setLastSavedAt(null)
      setHasPendingChanges(false)
      lastDraftDataRef.current = {}

      // Optionally delete from backend
      if (jobDraftId) {
        fetch(`${BACKEND_DRAFT_ENDPOINT}/${jobDraftId}`, {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json'
          }
        }).catch(error => {
          console.warn('Failed to delete draft from backend:', error)
        })
      }
    } catch (error) {
      console.error('Error clearing draft:', error)
    }
  }, [jobDraftId])

  // Get human-readable time since last save (for UI display)
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
