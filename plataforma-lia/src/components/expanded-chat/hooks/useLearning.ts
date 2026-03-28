/**
 * useLearning hook - Integrates with the Job Learning API
 * 
 * Provides:
 * - Wizard suggestions (salary, skills, behavioral, TTF)
 * - Similar jobs lookup
 * - Pattern-based recommendations
 */
import { useState, useCallback, useEffect, useRef } from 'react'

interface SalarySuggestion {
  has_suggestion: boolean
  min_salary?: number
  max_salary?: number
  median_salary?: number
  avg_salary?: number
  sample_count?: number
  confidence?: number
  basis?: string
  percentiles?: {
    p10?: number
    p25?: number
    p50?: number
    p75?: number
    p90?: number
  }
  message?: string
}

interface SkillRecommendation {
  name: string
  score: number
}

interface SkillsSuggestion {
  has_recommendations: boolean
  recommended_skills?: SkillRecommendation[]
  missing_critical?: string[]
  patterns_used?: number
  total_samples?: number
  confidence?: number
  message?: string
}

interface BehavioralRecommendation {
  name: string
  score: number
}

interface BehavioralSuggestion {
  has_recommendations: boolean
  recommended_behavioral?: BehavioralRecommendation[]
  patterns_used?: number
  message?: string
}

interface TimeToFillPrediction {
  has_prediction: boolean
  estimated_days?: number
  range_min?: number
  range_max?: number
  median_days?: number
  sample_count?: number
  confidence?: number
  factors?: string[]
  basis?: string
  message?: string
}

interface WizardSuggestions {
  has_suggestions: boolean
  salary: SalarySuggestion
  skills: SkillsSuggestion
  behavioral: BehavioralSuggestion
  time_to_fill: TimeToFillPrediction
  patterns_found: number
  total_samples: number
  generated_at: string
  error?: string
}

interface JobPattern {
  id: string
  company_id: string
  pattern_type: string
  pattern_key: string
  job_title_normalized: string
  department?: string
  seniority?: string
  sample_count: number
  success_count: number
  success_rate: number
  common_skills: string[]
  common_behavioral: string[]
  avg_time_to_fill?: number
  confidence: number
}

interface LearningState {
  suggestions: WizardSuggestions | null
  similarJobs: JobPattern[]
  isLoading: boolean
  error: string | null
  lastFetchedFor: string | null
}

interface LearningRequest {
  companyId: string
  jobTitle: string
  department?: string
  seniority?: string
  location?: string
  existingSkills?: string[]
  existingBehavioral?: string[]
}

const BACKEND_URL = '/api/backend-proxy'

export function useLearning() {
  const [state, setState] = useState<LearningState>({
    suggestions: null,
    similarJobs: [],
    isLoading: false,
    error: null,
    lastFetchedFor: null,
  })
  
  const abortControllerRef = useRef<AbortController | null>(null)
  
  // Use refs to track state for callback stability - prevents infinite loops
  // when fetchWizardSuggestions is used as a useEffect dependency
  const lastFetchedForRef = useRef<string | null>(null)
  const suggestionsRef = useRef<WizardSuggestions | null>(null)
  
  // Keep refs in sync with state
  lastFetchedForRef.current = state.lastFetchedFor
  suggestionsRef.current = state.suggestions
  
  const fetchWizardSuggestions = useCallback(async (request: LearningRequest) => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    
    abortControllerRef.current = new AbortController()
    
    const requestKey = `${request.jobTitle}_${request.department}_${request.seniority}`
    
    // Use refs instead of state to avoid recreating callback when state changes
    if (lastFetchedForRef.current === requestKey && suggestionsRef.current) {
      return suggestionsRef.current
    }
    
    setState(prev => ({ ...prev, isLoading: true, error: null }))
    
    try {
      const response = await fetch(`${BACKEND_URL}/learning/wizard-suggestions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          company_id: request.companyId,
          job_title: request.jobTitle,
          department: request.department,
          seniority: request.seniority,
          location: request.location,
          existing_skills: request.existingSkills || [],
          existing_behavioral: request.existingBehavioral || [],
        }),
        signal: abortControllerRef.current.signal,
      })
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }
      
      const data: WizardSuggestions = await response.json()
      
      setState(prev => ({
        ...prev,
        suggestions: data,
        isLoading: false,
        lastFetchedFor: requestKey,
      }))
      
      return data
      
    } catch (error) {
      if ((error as Error).name === 'AbortError') {
        return null
      }
      
      const errorMessage = (error as Error).message || 'Erro ao buscar sugestões'
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: errorMessage,
      }))
      
      return null
    }
  }, []) // Empty deps - uses refs for state comparison to prevent infinite loops
  
  const fetchSimilarJobs = useCallback(async (request: LearningRequest, limit = 5) => {
    try {
      const response = await fetch(`${BACKEND_URL}/learning/similar-jobs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          company_id: request.companyId,
          job_title: request.jobTitle,
          department: request.department,
          seniority: request.seniority,
          limit,
        }),
      })
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }
      
      const data = await response.json()
      
      setState(prev => ({
        ...prev,
        similarJobs: data.patterns || [],
      }))
      
      return data.patterns || []
      
    } catch (error) {
      return []
    }
  }, [])
  
  const fetchSalarySuggestion = useCallback(async (
    companyId: string,
    jobTitle: string,
    seniority?: string,
    location?: string,
    department?: string
  ): Promise<SalarySuggestion | null> => {
    try {
      const response = await fetch(`${BACKEND_URL}/learning/salary-suggestion`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          company_id: companyId,
          job_title: jobTitle,
          seniority,
          location,
          department,
        }),
      })
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }
      
      return await response.json()
      
    } catch (error) {
      return null
    }
  }, [])
  
  const fetchSkillsRecommendation = useCallback(async (
    companyId: string,
    jobTitle: string,
    existingSkills?: string[],
    department?: string,
    seniority?: string,
    limit = 10
  ): Promise<SkillsSuggestion | null> => {
    try {
      const response = await fetch(`${BACKEND_URL}/learning/skills-recommendation`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          company_id: companyId,
          job_title: jobTitle,
          existing_skills: existingSkills || [],
          department,
          seniority,
          limit,
        }),
      })
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }
      
      return await response.json()
      
    } catch (error) {
      return null
    }
  }, [])
  
  const fetchTimeToFill = useCallback(async (
    companyId: string,
    jobTitle: string,
    seniority?: string,
    location?: string,
    salaryMin?: number,
    salaryMax?: number
  ): Promise<TimeToFillPrediction | null> => {
    try {
      const response = await fetch(`${BACKEND_URL}/learning/time-to-fill`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          company_id: companyId,
          job_title: jobTitle,
          seniority,
          location,
          salary_min: salaryMin,
          salary_max: salaryMax,
        }),
      })
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }
      
      return await response.json()
      
    } catch (error) {
      return null
    }
  }, [])
  
  const recordJobOutcome = useCallback(async (
    companyId: string,
    jobId: string,
    outcomeData: Record<string, unknown>
  ) => {
    try {
      const response = await fetch(`${BACKEND_URL}/learning/record-outcome`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          company_id: companyId,
          job_id: jobId,
          ...outcomeData,
        }),
      })
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }
      
      return await response.json()
      
    } catch (error) {
      return null
    }
  }, [])
  
  const clearSuggestions = useCallback(() => {
    setState({
      suggestions: null,
      similarJobs: [],
      isLoading: false,
      error: null,
      lastFetchedFor: null,
    })
  }, [])
  
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
    }
  }, [])
  
  return {
    ...state,
    fetchWizardSuggestions,
    fetchSimilarJobs,
    fetchSalarySuggestion,
    fetchSkillsRecommendation,
    fetchTimeToFill,
    recordJobOutcome,
    clearSuggestions,
  }
}

export type {
  SalarySuggestion,
  SkillsSuggestion,
  BehavioralSuggestion,
  TimeToFillPrediction,
  WizardSuggestions,
  JobPattern,
  LearningRequest,
}
