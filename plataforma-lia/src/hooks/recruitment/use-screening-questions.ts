"use client"

import { useState, useCallback } from 'react'

import type { BigFiveProfile } from '@/hooks/company/use-company-culture'
export type { BigFiveProfile }

export interface ScreeningQuestion {
  id: string
  text: string
  category: 'behavioral' | 'technical' | 'cultural'
  trait?: string
  skill?: string
  bloom_level: number
  bloom_label: string
  dreyfus_stage: number
  dreyfus_label: string
  framework: 'CBI' | 'Bloom' | 'Dreyfus' | 'BigFive'
  weight: number
  expected_signals: string[]
  scoring_criteria: Record<string, string>
  is_selected: boolean
  order: number
}

export interface ScreeningQuestionRequest {
  title: string
  department?: string
  seniority: 'junior' | 'pleno' | 'senior' | 'lead' | 'executive'
  big_five_profile?: BigFiveProfile
  skills: string[]
  job_description?: string
  question_count?: number
}

export interface ScreeningQuestionsResponse {
  questions: ScreeningQuestion[]
  behavioral_questions: ScreeningQuestion[]
  technical_questions: ScreeningQuestion[]
  cultural_questions: ScreeningQuestion[]
  total_count: number
  metadata: {
    seniority: string
    dreyfus_stage: number
    bloom_levels: number[]
    skills_count: number
    title: string
    department?: string
  }
}

interface UseScreeningQuestionsResult {
  questions: ScreeningQuestion[]
  behavioralQuestions: ScreeningQuestion[]
  technicalQuestions: ScreeningQuestion[]
  culturalQuestions: ScreeningQuestion[]
  isLoading: boolean
  error: string | null
  metadata: ScreeningQuestionsResponse['metadata'] | null
  generateQuestions: (context: ScreeningQuestionRequest) => Promise<void>
  regenerateCategory: (category: 'behavioral' | 'technical' | 'cultural') => Promise<void>
  toggleQuestion: (questionId: string) => void
  getSelectedQuestions: () => ScreeningQuestion[]
  selectAll: (category?: 'behavioral' | 'technical' | 'cultural') => void
  deselectAll: (category?: 'behavioral' | 'technical' | 'cultural') => void
}

export function useScreeningQuestions(): UseScreeningQuestionsResult {
  const [questions, setQuestions] = useState<ScreeningQuestion[]>([])
  const [behavioralQuestions, setBehavioralQuestions] = useState<ScreeningQuestion[]>([])
  const [technicalQuestions, setTechnicalQuestions] = useState<ScreeningQuestion[]>([])
  const [culturalQuestions, setCulturalQuestions] = useState<ScreeningQuestion[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [metadata, setMetadata] = useState<ScreeningQuestionsResponse['metadata'] | null>(null)
  const [currentContext, setCurrentContext] = useState<ScreeningQuestionRequest | null>(null)

  const generateQuestions = useCallback(async (context: ScreeningQuestionRequest) => {
    setIsLoading(true)
    setError(null)
    setCurrentContext(context)

    try {
      const response = await fetch('/api/backend-proxy/screening/questions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(context),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `Failed to generate questions: ${response.status}`)
      }

      const data: ScreeningQuestionsResponse = await response.json()

      setQuestions(data.questions)
      setBehavioralQuestions(data.behavioral_questions)
      setTechnicalQuestions(data.technical_questions)
      setCulturalQuestions(data.cultural_questions)
      setMetadata(data.metadata)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setIsLoading(false)
    }
  }, [])

  const regenerateCategory = useCallback(async (category: 'behavioral' | 'technical' | 'cultural') => {
    if (!currentContext) {
      setError('No context available for regeneration')
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const existingIds = questions
        .filter(q => q.category === category)
        .map(q => q.id)

      const response = await fetch('/api/backend-proxy/screening/questions/regenerate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          context: currentContext,
          category,
          exclude_ids: existingIds,
        }),
      })

      if (!response.ok) {
        throw new Error(`Failed to regenerate questions: ${response.status}`)
      }

      const newQuestions: ScreeningQuestion[] = await response.json()

      setQuestions(prev => {
        const otherQuestions = prev.filter(q => q.category !== category)
        return [...otherQuestions, ...newQuestions]
      })

      if (category === 'behavioral') {
        setBehavioralQuestions(newQuestions)
      } else if (category === 'technical') {
        setTechnicalQuestions(newQuestions)
      } else if (category === 'cultural') {
        setCulturalQuestions(newQuestions)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setIsLoading(false)
    }
  }, [currentContext, questions])

  const toggleQuestion = useCallback((questionId: string) => {
    const updateQuestion = (q: ScreeningQuestion) =>
      q.id === questionId ? { ...q, is_selected: !q.is_selected } : q

    setQuestions(prev => prev.map(updateQuestion))
    setBehavioralQuestions(prev => prev.map(updateQuestion))
    setTechnicalQuestions(prev => prev.map(updateQuestion))
    setCulturalQuestions(prev => prev.map(updateQuestion))
  }, [])

  const getSelectedQuestions = useCallback(() => {
    return questions.filter(q => q.is_selected)
  }, [questions])

  const selectAll = useCallback((category?: 'behavioral' | 'technical' | 'cultural') => {
    const selectQuestion = (q: ScreeningQuestion) =>
      !category || q.category === category ? { ...q, is_selected: true } : q

    setQuestions(prev => prev.map(selectQuestion))
    if (!category || category === 'behavioral') {
      setBehavioralQuestions(prev => prev.map(q => ({ ...q, is_selected: true })))
    }
    if (!category || category === 'technical') {
      setTechnicalQuestions(prev => prev.map(q => ({ ...q, is_selected: true })))
    }
    if (!category || category === 'cultural') {
      setCulturalQuestions(prev => prev.map(q => ({ ...q, is_selected: true })))
    }
  }, [])

  const deselectAll = useCallback((category?: 'behavioral' | 'technical' | 'cultural') => {
    const deselectQuestion = (q: ScreeningQuestion) =>
      !category || q.category === category ? { ...q, is_selected: false } : q

    setQuestions(prev => prev.map(deselectQuestion))
    if (!category || category === 'behavioral') {
      setBehavioralQuestions(prev => prev.map(q => ({ ...q, is_selected: false })))
    }
    if (!category || category === 'technical') {
      setTechnicalQuestions(prev => prev.map(q => ({ ...q, is_selected: false })))
    }
    if (!category || category === 'cultural') {
      setCulturalQuestions(prev => prev.map(q => ({ ...q, is_selected: false })))
    }
  }, [])

  return {
    questions,
    behavioralQuestions,
    technicalQuestions,
    culturalQuestions,
    isLoading,
    error,
    metadata,
    generateQuestions,
    regenerateCategory,
    toggleQuestion,
    getSelectedQuestions,
    selectAll,
    deselectAll,
  }
}

export default useScreeningQuestions

// === WSI Screening Pipeline Types ===

export interface UnifiedScreeningQuestion {
  id: string
  text: string
  category: string
  block_id: number
  source: 'company' | 'wsi_generated'
  trait?: string
  skill?: string
  bloom_level: number
  bloom_label: string
  dreyfus_stage: number
  dreyfus_label: string
  framework: string
  weight: number
  expected_signals: string[]
  scoring_criteria: Record<string, string>
  is_selected: boolean
  is_eliminatory: boolean
  question_type: string
  options?: string[]
  expected_answer?: string
  order: number
}

export interface WSIBlockSummary {
  block_id: number
  block_name: string
  question_count: number
  questions: UnifiedScreeningQuestion[]
}

export interface WSIScreeningPipelineRequest {
  job_title: string
  department?: string
  seniority: 'junior' | 'pleno' | 'senior' | 'lead' | 'executive'
  technical_skills: string[]
  behavioral_competencies?: string[]
  responsibilities?: string[]
  big_five_profile?: BigFiveProfile
  job_description?: string
  question_count?: number
  format?: 'compact' | 'full'
  include_company_questions?: boolean
  company_question_categories?: string[]
  is_affirmative?: boolean
  affirmative_type?: string
}

export interface WSIScreeningPipelineResponse {
  success: boolean
  questions: UnifiedScreeningQuestion[]
  blocks: WSIBlockSummary[]
  total_count: number
  block_distribution: Record<string, number>
  metadata: {
    seniority: string
    dreyfus_stage: number
    bloom_levels: number[]
    skills_count: number
    title: string
    department?: string
    format: string
    company_questions_count: number
  }
  quality_warnings: string[]
}

interface UseWSIScreeningPipelineResult {
  questions: UnifiedScreeningQuestion[]
  blocks: WSIBlockSummary[]
  companyQuestions: UnifiedScreeningQuestion[]
  technicalQuestions: UnifiedScreeningQuestion[]
  behavioralQuestions: UnifiedScreeningQuestion[]
  isLoading: boolean
  error: string | null
  metadata: WSIScreeningPipelineResponse['metadata'] | null
  qualityWarnings: string[]
  totalCount: number
  blockDistribution: Record<string, number>
  generatePipeline: (context: WSIScreeningPipelineRequest) => Promise<void>
  toggleQuestion: (questionId: string) => void
  getSelectedQuestions: () => UnifiedScreeningQuestion[]
  selectAllInBlock: (blockId: number) => void
  deselectAllInBlock: (blockId: number) => void
}

export function useWSIScreeningPipeline(): UseWSIScreeningPipelineResult {
  const [questions, setQuestions] = useState<UnifiedScreeningQuestion[]>([])
  const [blocks, setBlocks] = useState<WSIBlockSummary[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [metadata, setMetadata] = useState<WSIScreeningPipelineResponse['metadata'] | null>(null)
  const [qualityWarnings, setQualityWarnings] = useState<string[]>([])
  const [totalCount, setTotalCount] = useState(0)
  const [blockDistribution, setBlockDistribution] = useState<Record<string, number>>({})

  const generatePipeline = useCallback(async (context: WSIScreeningPipelineRequest) => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch('/api/backend-proxy/wsi/screening-pipeline', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(context),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || errorData.error || `Failed to generate WSI pipeline: ${response.status}`)
      }

      const data: WSIScreeningPipelineResponse = await response.json()

      setQuestions(data.questions)
      setBlocks(data.blocks)
      setMetadata(data.metadata)
      setQualityWarnings(data.quality_warnings || [])
      setTotalCount(data.total_count)
      setBlockDistribution(data.block_distribution || {})
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setIsLoading(false)
    }
  }, [])

  const companyQuestions = questions.filter(q => q.block_id === 2)
  const technicalQuestions = questions.filter(q => q.block_id === 3)
  const behavioralQuestions = questions.filter(q => q.block_id === 4)

  const toggleQuestion = useCallback((questionId: string) => {
    setQuestions(prev =>
      prev.map(q =>
        q.id === questionId ? { ...q, is_selected: !q.is_selected } : q
      )
    )
    setBlocks(prev =>
      prev.map(block => ({
        ...block,
        questions: block.questions.map(q =>
          q.id === questionId ? { ...q, is_selected: !q.is_selected } : q
        ),
      }))
    )
  }, [])

  const getSelectedQuestions = useCallback(() => {
    return questions.filter(q => q.is_selected)
  }, [questions])

  const selectAllInBlock = useCallback((blockId: number) => {
    setQuestions(prev =>
      prev.map(q =>
        q.block_id === blockId ? { ...q, is_selected: true } : q
      )
    )
    setBlocks(prev =>
      prev.map(block =>
        block.block_id === blockId
          ? { ...block, questions: block.questions.map(q => ({ ...q, is_selected: true })) }
          : block
      )
    )
  }, [])

  const deselectAllInBlock = useCallback((blockId: number) => {
    setQuestions(prev =>
      prev.map(q =>
        q.block_id === blockId ? { ...q, is_selected: false } : q
      )
    )
    setBlocks(prev =>
      prev.map(block =>
        block.block_id === blockId
          ? { ...block, questions: block.questions.map(q => ({ ...q, is_selected: false })) }
          : block
      )
    )
  }, [])

  return {
    questions,
    blocks,
    companyQuestions,
    technicalQuestions,
    behavioralQuestions,
    isLoading,
    error,
    metadata,
    qualityWarnings,
    totalCount,
    blockDistribution,
    generatePipeline,
    toggleQuestion,
    getSelectedQuestions,
    selectAllInBlock,
    deselectAllInBlock,
  }
}
