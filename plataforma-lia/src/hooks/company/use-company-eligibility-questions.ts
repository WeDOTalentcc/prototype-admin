"use client"

import { useState, useCallback, useEffect } from 'react'

export interface CompanyEligibilityQuestion {
  id: string
  question_text: string
  question_type: 'text' | 'yes_no' | 'single_choice' | 'multiple_choice' | 'scale'
  options?: string[]
  category: string
  is_required: boolean
  is_eliminatory: boolean
  expected_answer?: string
  is_active: boolean
  order: number
  created_at?: string
  updated_at?: string
}

/** @deprecated Use CompanyEligibilityQuestion instead */
export type CompanyScreeningQuestion = CompanyEligibilityQuestion

interface UseCompanyEligibilityQuestionsResult {
  questions: CompanyEligibilityQuestion[]
  isLoading: boolean
  error: string | null
  fetchQuestions: () => Promise<void>
  refetch: () => Promise<void>
}

export function useCompanyEligibilityQuestions(): UseCompanyEligibilityQuestionsResult {
  const [questions, setQuestions] = useState<CompanyEligibilityQuestion[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchQuestions = useCallback(async () => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch('/api/backend-proxy/company/screening-questions', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        if (response.status === 404) {
          setQuestions([])
          return
        }
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `Failed to fetch company questions: ${response.status}`)
      }

      const data = await response.json()
      const activeQuestions = (data.items || data || []).filter(
        (q: CompanyEligibilityQuestion) => q.is_active !== false
      )
      setQuestions(activeQuestions)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
      setQuestions([])
    } finally {
      setIsLoading(false)
    }
  }, [])

  const refetch = useCallback(async () => {
    await fetchQuestions()
  }, [fetchQuestions])

  useEffect(() => {
    fetchQuestions()
  }, [fetchQuestions])

  return {
    questions,
    isLoading,
    error,
    fetchQuestions,
    refetch,
  }
}

/** @deprecated Use useCompanyEligibilityQuestions instead */
export function useCompanyScreeningQuestions(): UseCompanyEligibilityQuestionsResult {
  return useCompanyEligibilityQuestions()
}

export default useCompanyEligibilityQuestions
