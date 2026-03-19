/**
 * useWizardAnalytics hook - Tracks wizard performance
 * 
 * Provides:
 * - Session tracking with stage timing
 * - Field update tracking (auto-fill vs manual)
 * - Suggestion acceptance tracking
 * - Performance metrics
 */
import { useState, useCallback, useEffect, useRef } from 'react'

interface StageTime {
  stage: string
  startedAt: number
  endedAt?: number
  durationMs?: number
}

interface FieldUpdate {
  field: string
  source: 'auto' | 'catalog' | 'pattern' | 'suggestion' | 'panel' | 'chat' | 'manual'
  timestamp: number
}

interface SuggestionEvent {
  type: string
  accepted: boolean
  timestamp: number
}

interface WizardSessionMetrics {
  sessionId: string
  companyId: string
  recruiterId: string
  startedAt: number
  endedAt?: number
  totalTimeMs: number
  stageTimings: Record<string, number>
  fieldsAutoFilled: number
  fieldsEdited: number
  totalFields: number
  autoFillRate: number
  editRate: number
  suggestionsShown: number
  suggestionsAccepted: number
  suggestionAcceptanceRate: number
}

interface AnalyticsState {
  sessionId: string | null
  isTracking: boolean
  currentStage: string | null
  stageTimes: StageTime[]
  fieldUpdates: FieldUpdate[]
  suggestions: SuggestionEvent[]
  startedAt: number | null
}

const BACKEND_URL = '/api/backend-proxy'

const ANALYTICS_ENABLED = false

export function useWizardAnalytics(companyId?: string, recruiterId?: string) {
  const [state, setState] = useState<AnalyticsState>({
    sessionId: null,
    isTracking: false,
    currentStage: null,
    stageTimes: [],
    fieldUpdates: [],
    suggestions: [],
    startedAt: null,
  })
  
  const sendEventRef = useRef<(endpoint: string, data: Record<string, unknown>) => Promise<void>>(
    async () => {}
  )
  
  sendEventRef.current = async (endpoint: string, data: Record<string, unknown>) => {
    if (!ANALYTICS_ENABLED) return
    
    try {
      const response = await fetch(`${BACKEND_URL}/wizard-analytics${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      })
      if (response.status === 404) {
        return
      }
    } catch {
      // Silently ignore analytics errors
    }
  }
  
  const startSession = useCallback(() => {
    if (!companyId || !recruiterId) {
      console.warn('Cannot start analytics session without companyId and recruiterId')
      return null
    }
    
    const sessionId = crypto.randomUUID()
    const now = Date.now()
    
    setState({
      sessionId,
      isTracking: true,
      currentStage: null,
      stageTimes: [],
      fieldUpdates: [],
      suggestions: [],
      startedAt: now,
    })
    
    sendEventRef.current?.('/session/start', {
      session_id: sessionId,
      company_id: companyId,
      recruiter_id: recruiterId,
    })
    
    return sessionId
  }, [companyId, recruiterId])
  
  const trackStageChange = useCallback((stage: string) => {
    setState(prev => {
      if (!prev.isTracking) return prev
      
      const now = Date.now()
      const updatedStageTimes = [...prev.stageTimes]
      
      if (prev.currentStage) {
        const currentStageIndex = updatedStageTimes.findIndex(
          st => st.stage === prev.currentStage && !st.endedAt
        )
        if (currentStageIndex >= 0) {
          updatedStageTimes[currentStageIndex] = {
            ...updatedStageTimes[currentStageIndex],
            endedAt: now,
            durationMs: now - updatedStageTimes[currentStageIndex].startedAt,
          }
        }
      }
      
      updatedStageTimes.push({
        stage,
        startedAt: now,
      })
      
      if (prev.sessionId) {
        sendEventRef.current?.('/session/stage', {
          session_id: prev.sessionId,
          stage,
        })
      }
      
      return {
        ...prev,
        currentStage: stage,
        stageTimes: updatedStageTimes,
      }
    })
  }, [])
  
  const trackFieldUpdate = useCallback((
    field: string,
    source: FieldUpdate['source']
  ) => {
    setState(prev => {
      if (!prev.isTracking) return prev
      
      const update: FieldUpdate = {
        field,
        source,
        timestamp: Date.now(),
      }
      
      if (prev.sessionId) {
        sendEventRef.current?.('/session/field', {
          session_id: prev.sessionId,
          field,
          source,
        })
      }
      
      return {
        ...prev,
        fieldUpdates: [...prev.fieldUpdates, update],
      }
    })
  }, [])
  
  const trackSuggestion = useCallback((type: string, accepted: boolean) => {
    setState(prev => {
      if (!prev.isTracking) return prev
      
      const event: SuggestionEvent = {
        type,
        accepted,
        timestamp: Date.now(),
      }
      
      if (prev.sessionId) {
        sendEventRef.current?.('/session/suggestion', {
          session_id: prev.sessionId,
          suggestion_type: type,
          accepted,
        })
      }
      
      return {
        ...prev,
        suggestions: [...prev.suggestions, event],
      }
    })
  }, [])
  
  const completeSession = useCallback(async (jobId?: string): Promise<WizardSessionMetrics | null> => {
    if (!state.sessionId || !state.startedAt || !companyId || !recruiterId) {
      return null
    }
    
    const now = Date.now()
    const totalTimeMs = now - state.startedAt
    
    const updatedStageTimes = [...state.stageTimes]
    if (state.currentStage) {
      const currentStageIndex = updatedStageTimes.findIndex(
        st => st.stage === state.currentStage && !st.endedAt
      )
      if (currentStageIndex >= 0) {
        updatedStageTimes[currentStageIndex] = {
          ...updatedStageTimes[currentStageIndex],
          endedAt: now,
          durationMs: now - updatedStageTimes[currentStageIndex].startedAt,
        }
      }
    }
    
    const stageTimings: Record<string, number> = {}
    for (const st of updatedStageTimes) {
      if (st.durationMs) {
        stageTimings[st.stage] = (stageTimings[st.stage] || 0) + st.durationMs
      }
    }
    
    const fieldsAutoFilled = state.fieldUpdates.filter(
      f => ['auto', 'catalog', 'pattern', 'suggestion'].includes(f.source)
    ).length
    
    const fieldsEdited = state.fieldUpdates.filter(
      f => ['panel', 'chat', 'manual'].includes(f.source)
    ).length
    
    const totalFields = fieldsAutoFilled + fieldsEdited
    const autoFillRate = totalFields > 0 ? fieldsAutoFilled / totalFields : 0
    const editRate = totalFields > 0 ? fieldsEdited / totalFields : 0
    
    const suggestionsShown = state.suggestions.length
    const suggestionsAccepted = state.suggestions.filter(s => s.accepted).length
    const suggestionAcceptanceRate = suggestionsShown > 0 ? suggestionsAccepted / suggestionsShown : 0
    
    const metrics: WizardSessionMetrics = {
      sessionId: state.sessionId,
      companyId,
      recruiterId,
      startedAt: state.startedAt,
      endedAt: now,
      totalTimeMs,
      stageTimings,
      fieldsAutoFilled,
      fieldsEdited,
      totalFields,
      autoFillRate: Math.round(autoFillRate * 100) / 100,
      editRate: Math.round(editRate * 100) / 100,
      suggestionsShown,
      suggestionsAccepted,
      suggestionAcceptanceRate: Math.round(suggestionAcceptanceRate * 100) / 100,
    }
    
    // Analytics is disabled - skip network calls
    if (ANALYTICS_ENABLED) {
      try {
        await fetch(`${BACKEND_URL}/wizard-analytics/session/complete`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            session_id: state.sessionId,
            job_id: jobId,
          }),
        })
      } catch {
        // Silently ignore analytics errors
      }
    }
    
    setState({
      sessionId: null,
      isTracking: false,
      currentStage: null,
      stageTimes: [],
      fieldUpdates: [],
      suggestions: [],
      startedAt: null,
    })
    
    return metrics
  }, [state, companyId, recruiterId])
  
  const getMetrics = useCallback((): Partial<WizardSessionMetrics> => {
    if (!state.startedAt) {
      return {}
    }
    
    const now = Date.now()
    const totalTimeMs = now - state.startedAt
    
    const fieldsAutoFilled = state.fieldUpdates.filter(
      f => ['auto', 'catalog', 'pattern', 'suggestion'].includes(f.source)
    ).length
    
    const fieldsEdited = state.fieldUpdates.filter(
      f => ['panel', 'chat', 'manual'].includes(f.source)
    ).length
    
    const totalFields = fieldsAutoFilled + fieldsEdited
    const autoFillRate = totalFields > 0 ? fieldsAutoFilled / totalFields : 0
    
    const suggestionsShown = state.suggestions.length
    const suggestionsAccepted = state.suggestions.filter(s => s.accepted).length
    const suggestionAcceptanceRate = suggestionsShown > 0 ? suggestionsAccepted / suggestionsShown : 0
    
    return {
      sessionId: state.sessionId || undefined,
      totalTimeMs,
      fieldsAutoFilled,
      fieldsEdited,
      totalFields,
      autoFillRate: Math.round(autoFillRate * 100) / 100,
      suggestionsShown,
      suggestionsAccepted,
      suggestionAcceptanceRate: Math.round(suggestionAcceptanceRate * 100) / 100,
    }
  }, [state])
  
  // Analytics cleanup disabled - no network calls on unmount
  // When ANALYTICS_ENABLED is true, this would send session completion
  useEffect(() => {
    return () => {
      // Analytics disabled - skip cleanup network calls
    }
  }, [])
  
  return {
    sessionId: state.sessionId,
    isTracking: state.isTracking,
    currentStage: state.currentStage,
    startSession,
    trackStageChange,
    trackFieldUpdate,
    trackSuggestion,
    completeSession,
    getMetrics,
  }
}

export type {
  WizardSessionMetrics,
  FieldUpdate,
  SuggestionEvent,
}
