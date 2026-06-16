import { useState, useEffect, useCallback } from "react"

export interface SuggestionCard {
  id: string
  type: string
  icon: string
  title: string
  description: string
  action: string
  priority: string
  category: string
  metadata?: Record<string, unknown>
}

export interface SuggestionsResponse {
  suggestions: SuggestionCard[]
  generated_at: string
  context?: Record<string, unknown>
}

export interface WizardStepRequest {
  conversation_id?: string
  stage: number
  user_input: string
  context?: Record<string, unknown>
}

export interface WizardStepResponse {
  conversation_id: string
  current_stage: number
  next_stage?: number
  stage_name: string
  lia_message: string
  detected_criteria?: Record<string, unknown>
  is_complete: boolean
  created_job?: Record<string, unknown>
}

export interface InsightItem {
  type: string
  title: string
  description: string
  severity: string
  recommendation?: string
  data?: Record<string, unknown>
}

export interface InsightsResponse {
  insights: InsightItem[]
  summary: Record<string, unknown>
  generated_at: string
}

export interface ExpandedPromptRequest {
  message: string
  context_type: string
  context_ids?: string[]
  context?: Record<string, unknown>
}

export interface ExpandedPromptResponse {
  response: string
  agent_used: string
  actions?: Array<Record<string, unknown>>
  follow_up_suggestions?: string[]
}

export function useLiaSuggestions(companyId: string = "", limit: number = 6) {
  const [suggestions, setSuggestions] = useState<SuggestionCard[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [context, setContext] = useState<Record<string, unknown> | null>(null)

  const fetchSuggestions = useCallback(async (signal?: AbortSignal) => {
    setLoading(true)
    setError(null)
    
    try {
      const params = new URLSearchParams({
        company_id: companyId,
        limit: limit.toString(),
      })
      
      const response = await fetch(`/api/backend-proxy/lia/suggestions?${params.toString()}`, { signal })
      
      if (!response.ok) {
        throw new Error("Failed to fetch suggestions")
      }
      
      const data: SuggestionsResponse = await response.json()
      setSuggestions(data.suggestions)
      setContext(data.context || null)
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') return
      setError(err instanceof Error ? err.message : "Unknown error")
      setSuggestions([])
    } finally {
      setLoading(false)
    }
  }, [companyId, limit])

  useEffect(() => {
    const controller = new AbortController()
    fetchSuggestions(controller.signal)
    return () => controller.abort()
  }, [fetchSuggestions])

  return {
    suggestions,
    loading,
    error,
    context,
    refresh: fetchSuggestions,
  }
}

export function useJobWizard() {
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [liaMessage, setLiaMessage] = useState<string>("")
  const [detectedCriteria, setDetectedCriteria] = useState<Record<string, unknown> | null>(null)
  const [isComplete, setIsComplete] = useState(false)

  // Map frontend stage names to backend stage numbers
  const stageNameToNumber: Record<string, number> = {
    'description': 1,
    'basic-info': 2,
    'competencies': 3,
    'salary': 4,
    'wsi-questions': 5,
    'review': 6,
    'pre-publish': 7,
    'candidate-search': 8,
    'calibration': 9,
    'active-search': 10
  }

  const processStep = useCallback(async (userInput: string, context?: Record<string, unknown>) => {
    setLoading(true)
    setError(null)
    
    try {
      // Get stage number from context or default to 1
      const currentStageName = context?.currentStage as string || 'description'
      const stageNumber = stageNameToNumber[currentStageName] || 1
      
      const request: WizardStepRequest = {
        conversation_id: conversationId || undefined,
        stage: stageNumber,
        user_input: userInput,
        context,
      }
      
      const response = await fetch("/api/backend-proxy/lia/job-wizard/step", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(request),
      })
      
      if (!response.ok) {
        throw new Error("Failed to process wizard step")
      }
      
      const data: WizardStepResponse = await response.json()
      
      setConversationId(data.conversation_id)
      setLiaMessage(data.lia_message)
      setDetectedCriteria(data.detected_criteria || null)
      setIsComplete(data.is_complete)
      
      return data
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error")
      return null
    } finally {
      setLoading(false)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [conversationId])

  const reset = useCallback(() => {
    setConversationId(null)
    setLiaMessage("")
    setDetectedCriteria(null)
    setIsComplete(false)
    setError(null)
  }, [])

  return {
    conversationId,
    loading,
    error,
    liaMessage,
    detectedCriteria,
    isComplete,
    processStep,
    reset,
  }
}

export function useJobInsights() {
  const [insights, setInsights] = useState<InsightItem[]>([])
  const [summary, setSummary] = useState<Record<string, unknown> | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const generateInsights = useCallback(async (jobIds: string[], insightTypes?: string[]) => {
    if (jobIds.length === 0) {
      setInsights([])
      setSummary(null)
      return null
    }
    
    setLoading(true)
    setError(null)
    
    try {
      const response = await fetch("/api/backend-proxy/lia/job-insights", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          job_ids: jobIds,
          insight_types: insightTypes,
        }),
      })
      
      if (!response.ok) {
        throw new Error("Failed to generate insights")
      }
      
      const data: InsightsResponse = await response.json()
      setInsights(data.insights)
      setSummary(data.summary)
      
      return data
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error")
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  return {
    insights,
    summary,
    loading,
    error,
    generateInsights,
  }
}

export function useLiaExpandedPrompt() {
  const [response, setResponse] = useState<string>("")
  const [agentUsed, setAgentUsed] = useState<string>("")
  const [followUpSuggestions, setFollowUpSuggestions] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const sendPrompt = useCallback(async (
    message: string,
    contextType: string,
    contextIds?: string[],
    context?: Record<string, unknown>
  ) => {
    setLoading(true)
    setError(null)
    
    try {
      const request: ExpandedPromptRequest = {
        message,
        context_type: contextType,
        context_ids: contextIds,
        context,
      }
      
      const res = await fetch("/api/backend-proxy/lia/expanded-prompt", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(request),
      })
      
      if (!res.ok) {
        throw new Error("Failed to process prompt")
      }
      
      const data: ExpandedPromptResponse = await res.json()
      setResponse(data.response)
      setAgentUsed(data.agent_used)
      setFollowUpSuggestions(data.follow_up_suggestions || [])
      
      return data
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error")
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  const reset = useCallback(() => {
    setResponse("")
    setAgentUsed("")
    setFollowUpSuggestions([])
    setError(null)
  }, [])

  return {
    response,
    agentUsed,
    followUpSuggestions,
    loading,
    error,
    sendPrompt,
    reset,
  }
}
