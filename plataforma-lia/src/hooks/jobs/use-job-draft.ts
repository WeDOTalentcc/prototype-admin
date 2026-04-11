"use client"

import { useState, useCallback, useMemo } from 'react'

export type FieldSource = 'inferred' | 'company_default' | 'benchmark' | 'manual'

interface BackendDraftField {
  id?: string
  field?: string
  type?: string
  name?: string
  label?: string
  value?: unknown
  data?: unknown
  confidence?: number
  confirmed?: boolean
  category?: string
}

export interface JobDraftField {
  id: string
  field: string
  label: string
  value: unknown
  confidence: number
  source: FieldSource
  confirmed: boolean
  category?: string
}

export interface JobDraftState {
  inferredCriteria: JobDraftField[]
  companyDefaults: JobDraftField[]
  suggestions: JobDraftField[]
  unifiedTitle: string | null
  needsConfirmation: string[]
}

export interface CompetencyValidation {
  isValid: boolean
  techCount: number
  behavioralCount: number
  totalCount: number
  minRequired: number
  message: string | null
}

const MIN_COMPETENCIES_REQUIRED = 3

interface UseJobDraftResult {
  state: JobDraftState
  initializeFromBackend: (data: {
    inferred_criteria?: BackendDraftField[]
    company_defaults?: BackendDraftField[]
    suggested_from_benchmark?: BackendDraftField[]
    unified_title?: string
    needs_confirmation?: string[]
  }) => void
  confirmField: (fieldId: string) => void
  rejectField: (fieldId: string) => void
  updateField: (fieldId: string, value: unknown) => void
  getFieldsBySource: (source: FieldSource) => JobDraftField[]
  getFieldsByCategory: (category: string) => JobDraftField[]
  getAllConfirmedFields: () => JobDraftField[]
  getAllPendingFields: () => JobDraftField[]
  validateMinCompetencies: (selectedTechSkills: unknown[], selectedBehavioralCompetencies: unknown[]) => CompetencyValidation
  getConfidenceLevel: (confidence: number) => 'high' | 'medium' | 'low'
  reset: () => void
}

const initialState: JobDraftState = {
  inferredCriteria: [],
  companyDefaults: [],
  suggestions: [],
  unifiedTitle: null,
  needsConfirmation: []
}

function mapBackendFieldToJobDraftField(
  field: BackendDraftField, 
  source: FieldSource, 
  index: number
): JobDraftField {
  return {
    id: field.id || `${source}-${index}-${Date.now()}`,
    field: field.field || field.type || field.name || 'unknown',
    label: field.label || field.field || field.name || 'Campo',
    value: field.value ?? field.data ?? field,
    confidence: typeof field.confidence === 'number' ? field.confidence : 0.5,
    source,
    confirmed: field.confirmed ?? false,
    category: field.category || field.type || undefined
  }
}

export function useJobDraft(): UseJobDraftResult {
  const [state, setState] = useState<JobDraftState>(initialState)

  const initializeFromBackend = useCallback((data: {
    inferred_criteria?: BackendDraftField[]
    company_defaults?: BackendDraftField[]
    suggested_from_benchmark?: BackendDraftField[]
    unified_title?: string
    needs_confirmation?: string[]
  }) => {
    const inferredCriteria = (data.inferred_criteria || []).map((field, idx) => 
      mapBackendFieldToJobDraftField(field, 'inferred', idx)
    )
    
    const companyDefaults = (data.company_defaults || []).map((field, idx) => 
      mapBackendFieldToJobDraftField(field, 'company_default', idx)
    )
    
    const suggestions = (data.suggested_from_benchmark || []).map((field, idx) => 
      mapBackendFieldToJobDraftField(field, 'benchmark', idx)
    )

    setState({
      inferredCriteria,
      companyDefaults,
      suggestions,
      unifiedTitle: data.unified_title || null,
      needsConfirmation: data.needs_confirmation || []
    })
  }, [])

  const updateFieldInArrays = useCallback((
    fieldId: string, 
    updater: (field: JobDraftField) => JobDraftField
  ) => {
    setState(prev => ({
      ...prev,
      inferredCriteria: prev.inferredCriteria.map(f => f.id === fieldId ? updater(f) : f),
      companyDefaults: prev.companyDefaults.map(f => f.id === fieldId ? updater(f) : f),
      suggestions: prev.suggestions.map(f => f.id === fieldId ? updater(f) : f)
    }))
  }, [])

  const confirmField = useCallback((fieldId: string) => {
    updateFieldInArrays(fieldId, field => ({ ...field, confirmed: true }))
  }, [updateFieldInArrays])

  const rejectField = useCallback((fieldId: string) => {
    setState(prev => ({
      ...prev,
      inferredCriteria: prev.inferredCriteria.filter(f => f.id !== fieldId),
      companyDefaults: prev.companyDefaults.filter(f => f.id !== fieldId),
      suggestions: prev.suggestions.filter(f => f.id !== fieldId)
    }))
  }, [])

  const updateField = useCallback((fieldId: string, value: unknown) => {
    updateFieldInArrays(fieldId, field => ({ 
      ...field, 
      value, 
      source: 'manual' as FieldSource,
      confirmed: true 
    }))
  }, [updateFieldInArrays])

  const getFieldsBySource = useCallback((source: FieldSource): JobDraftField[] => {
    const allFields = [
      ...state.inferredCriteria,
      ...state.companyDefaults,
      ...state.suggestions
    ]
    return allFields.filter(f => f.source === source)
  }, [state])

  const getFieldsByCategory = useCallback((category: string): JobDraftField[] => {
    const allFields = [
      ...state.inferredCriteria,
      ...state.companyDefaults,
      ...state.suggestions
    ]
    return allFields.filter(f => f.category === category)
  }, [state])

  const getAllConfirmedFields = useCallback((): JobDraftField[] => {
    const allFields = [
      ...state.inferredCriteria,
      ...state.companyDefaults,
      ...state.suggestions
    ]
    return allFields.filter(f => f.confirmed)
  }, [state])

  const getAllPendingFields = useCallback((): JobDraftField[] => {
    const allFields = [
      ...state.inferredCriteria,
      ...state.companyDefaults,
      ...state.suggestions
    ]
    return allFields.filter(f => !f.confirmed)
  }, [state])

  const validateMinCompetencies = useCallback((
    selectedTechSkills: unknown[], 
    selectedBehavioralCompetencies: unknown[]
  ): CompetencyValidation => {
    const techCount = selectedTechSkills.length
    const behavioralCount = selectedBehavioralCompetencies.length
    const totalCount = techCount + behavioralCount
    const isValid = totalCount >= MIN_COMPETENCIES_REQUIRED

    return {
      isValid,
      techCount,
      behavioralCount,
      totalCount,
      minRequired: MIN_COMPETENCIES_REQUIRED,
      message: isValid 
        ? null 
        : `Adicione pelo menos ${MIN_COMPETENCIES_REQUIRED} competências para que a IA possa aprender seu padrão de contratação`
    }
  }, [])

  const getConfidenceLevel = useCallback((confidence: number): 'high' | 'medium' | 'low' => {
    if (confidence >= 0.85) return 'high'
    if (confidence >= 0.70) return 'medium'
    return 'low'
  }, [])

  const reset = useCallback(() => {
    setState(initialState)
  }, [])

  return {
    state,
    initializeFromBackend,
    confirmField,
    rejectField,
    updateField,
    getFieldsBySource,
    getFieldsByCategory,
    getAllConfirmedFields,
    getAllPendingFields,
    validateMinCompetencies,
    getConfidenceLevel,
    reset
  }
}

export default useJobDraft
