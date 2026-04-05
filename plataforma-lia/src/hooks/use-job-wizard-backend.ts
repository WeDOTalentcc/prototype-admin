import { useState, useCallback } from 'react'
import type { CompensationAnalysisResult, SalaryRange, BenefitItem, DataSource, CompetitivenessStatus } from '@/components/job-creation/compensation-analysis-panel'

// Backend schema types (snake_case)
interface BackendSalaryAnalysis {
  proposed_min?: number
  proposed_max?: number
  market_min?: number
  market_max?: number
  market_percentile?: number
  policy_min?: number
  policy_max?: number
  suggested_min?: number
  suggested_max?: number
  data_sources?: string[]
}

interface BackendBonusAnalysis {
  proposed_pct?: number
  policy_target_pct?: number
  proposed_criteria?: string
  suggested_pct?: number
  data_source?: string
}

interface BackendBenefitAnalysis {
  proposed_benefits?: string[]
  company_standard_benefits?: string[]
  monetizable_annual_value?: number
  missing_standard_benefits?: string[]
  data_source?: string
}

interface BackendTotalCompAnalysis {
  proposed_total_comp_min?: number
  proposed_total_comp_max?: number
  market_total_comp_min?: number
  market_total_comp_max?: number
  policy_total_comp_min?: number
  policy_total_comp_max?: number
  breakdown_chart?: Record<string, number>
}

interface BackendCompensationAnalysis {
  salary?: BackendSalaryAnalysis
  bonus?: BackendBonusAnalysis
  benefits?: BackendBenefitAnalysis
  total_comp?: BackendTotalCompAnalysis
  overall_assessment?: string
  summary?: string
}

// Transform backend snake_case to frontend camelCase
function transformCompensationAnalysis(backend: BackendCompensationAnalysis | undefined): CompensationAnalysisResult | undefined {
  if (!backend) return undefined
  
  const mapStatus = (status?: string): CompetitivenessStatus => {
    if (status === 'below_market' || status === 'below_policy') return 'below_market'
    if (status === 'above_market' || status === 'above_policy') return 'above_market'
    return 'competitive'
  }
  
  const mapDataSource = (source?: string): DataSource => {
    if (source === 'company_policy') return 'company_policy'
    if (source === 'market_benchmark') return 'market_benchmark'
    if (source === 'internal_history') return 'internal_history'
    if (source === 'inference') return 'inference'
    return 'user_input'
  }
  
  const salary = backend.salary || {}
  const bonus = backend.bonus || {}
  const benefits = backend.benefits || {}
  const totalComp = backend.total_comp || {}
  
  // Calculate percentages for breakdown
  const totalAnnual = (totalComp.proposed_total_comp_min || 0) + (totalComp.proposed_total_comp_max || 0)
  const salaryAnnual = ((salary.proposed_min || 0) + (salary.proposed_max || 0)) * 12
  const bonusAnnual = salaryAnnual * ((bonus.proposed_pct || 0) / 100)
  const benefitsAnnual = benefits.monetizable_annual_value || 0
  const totalValue = salaryAnnual + bonusAnnual + benefitsAnnual
  
  // Map proposed benefits to BenefitItem format
  const proposedBenefits: BenefitItem[] = (benefits.proposed_benefits || []).map((name, i) => ({
    id: `prop-${i}`,
    name,
    included: true,
    isCompanyStandard: (benefits.company_standard_benefits || []).includes(name)
  }))
  
  // Map company standard benefits
  const standardBenefits: BenefitItem[] = (benefits.company_standard_benefits || []).map((name, i) => ({
    id: `std-${i}`,
    name,
    included: (benefits.proposed_benefits || []).includes(name),
    isCompanyStandard: true
  }))
  
  // Map missing benefits
  const missingBenefits: BenefitItem[] = (benefits.missing_standard_benefits || []).map((name, i) => ({
    id: `miss-${i}`,
    name,
    included: false,
    isCompanyStandard: true
  }))
  
  return {
    overallStatus: mapStatus(backend.overall_assessment),
    executiveSummary: backend.summary || 'Análise de compensação baseada em dados de mercado e políticas da empresa.',
    salary: {
      proposed: { min: salary.proposed_min || 0, max: salary.proposed_max || 0 },
      market: { min: salary.market_min || 0, max: salary.market_max || 0 },
      policy: salary.policy_min ? { min: salary.policy_min, max: salary.policy_max || salary.policy_min } : undefined,
      source: mapDataSource((salary.data_sources || [])[0]),
      percentileVsMarket: salary.market_percentile || 50,
      suggestion: salary.suggested_min ? { min: salary.suggested_min, max: salary.suggested_max || salary.suggested_min } : undefined
    },
    bonus: {
      proposedPercentage: bonus.proposed_pct || 0,
      policyPercentage: bonus.policy_target_pct,
      criteria: bonus.proposed_criteria,
      source: mapDataSource(bonus.data_source),
      suggestion: bonus.suggested_pct
    },
    benefits: {
      proposed: proposedBenefits,
      companyStandard: standardBenefits,
      totalAnnualValue: benefitsAnnual,
      missingFromStandard: missingBenefits,
      source: mapDataSource(benefits.data_source)
    },
    totalCompensation: {
      proposedAnnual: totalValue || (totalComp.proposed_total_comp_min || 0),
      marketAnnual: totalComp.market_total_comp_min,
      policyAnnual: totalComp.policy_total_comp_min,
      breakdown: {
        salaryPercentage: totalValue > 0 ? Math.round((salaryAnnual / totalValue) * 100) : 70,
        bonusPercentage: totalValue > 0 ? Math.round((bonusAnnual / totalValue) * 100) : 15,
        benefitsPercentage: totalValue > 0 ? Math.round((benefitsAnnual / totalValue) * 100) : 15
      }
    }
  }
}

export interface DetectedCriteria {
  job_title?: string
  seniority?: string
  department?: string
  manager?: string
  manager_email?: string
  recruiter?: string
  recruiter_email?: string
  responsibilities?: string[]
  technical_skills?: string[]
  behavioral_skills?: string[]
  salary_min?: number
  salary_max?: number
  work_model?: string
  location?: string
  employment_type?: string
  deadline_screening?: string
  deadline_shortlist?: string
  deadline_closing?: string
  deadline?: string
  is_confidential?: boolean
  visibility?: 'public' | 'internal' | 'confidential' | 'hidden'
  whatsapp_template_type?: 'cold' | 'confidential' | 'warm'
  pipeline_template_id?: string
  // Affirmative Action
  is_affirmative?: boolean
  affirmative_criteria_primary?: 'gender' | 'race_ethnicity' | 'disability' | 'age' | 'lgbtqia' | 'refugee' | 'indigenous' | 'other'
  affirmative_criteria_secondary?: 'gender' | 'race_ethnicity' | 'disability' | 'age' | 'lgbtqia' | 'refugee' | 'indigenous' | 'other'
  affirmative_description?: string
}

export interface PeopleInfo {
  manager?: {
    name?: string
    email?: string
    inferred?: boolean
    department?: string
  }
  recruiter?: {
    name?: string
    email?: string
    auto_filled?: boolean
  }
}

export interface DeadlineInfo {
  deadline_screening?: string
  deadline_shortlist?: string
  deadline_closing?: string
  deadline?: string
  pipeline_name?: string
  source?: 'pipeline_sla' | 'default' | 'manual'
  total_days?: number
}

interface FieldOrigin {
  source: 'detected' | 'default' | 'manual' | 'suggested' | 'benchmark'
  confidence: number
  original_text?: string
}

interface WizardStepResponse {
  conversation_id: string
  current_stage: number
  next_stage?: number
  stage_name: string
  lia_message: string
  detected_criteria?: DetectedCriteria
  field_origins?: Record<string, FieldOrigin>
  is_complete: boolean
  created_job?: Record<string, unknown>
  intent_detected?: string
  benchmarks?: Record<string, unknown>
  suggestions?: Record<string, unknown>
}

export interface EvaluationStepResponse {
  conversation_id: string
  detected_criteria?: DetectedCriteria
  field_origins?: Record<string, FieldOrigin>
  compensation_analysis?: CompensationAnalysisResult
  lia_message?: string
  suggestions?: Record<string, unknown>
}

interface UseJobWizardBackendOptions {
  companyId?: string
  onCriteriaDetected?: (criteria: DetectedCriteria, origins: Record<string, FieldOrigin>) => void
  onError?: (error: Error) => void
}

// Skills deduplication types
interface DeduplicatedSkill {
  id: string
  name: string
  type: 'technical' | 'behavioral'
  times_confirmed: number
  is_promoted: boolean
  confidence: number
}

interface DeduplicatedSkillsResponse {
  skills: DeduplicatedSkill[]
  total: number
}

export function useJobWizardBackend(options: UseJobWizardBackendOptions = {}) {
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [isEvaluating, setIsEvaluating] = useState(false)
  const [isFetchingSkills, setIsFetchingSkills] = useState(false)
  const [deduplicatedSkills, setDeduplicatedSkills] = useState<DeduplicatedSkill[]>([])
  const [lastResponse, setLastResponse] = useState<WizardStepResponse | null>(null)
  const [evaluationResult, setEvaluationResult] = useState<EvaluationStepResponse | null>(null)
  const [error, setError] = useState<Error | null>(null)

  const processStep = useCallback(async (
    stage: number,
    userInput: string,
    context?: Record<string, unknown>
  ): Promise<WizardStepResponse | null> => {
    setIsProcessing(true)
    setError(null)

    try {
      const response = await fetch('/api/backend-proxy/lia/job-wizard/step', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          conversation_id: conversationId,
          stage,
          user_input: userInput,
          context
        })
      })

      if (!response.ok) {
        throw new Error(`Backend error: ${response.status}`)
      }

      const data: WizardStepResponse = await response.json()
      
      setConversationId(data.conversation_id)
      setLastResponse(data)

      if (data.detected_criteria && options.onCriteriaDetected) {
        options.onCriteriaDetected(
          data.detected_criteria,
          data.field_origins || {}
        )
      }

      return data
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Unknown error')
      setError(error)
      options.onError?.(error)
      return null
    } finally {
      setIsProcessing(false)
    }
  }, [conversationId, options])

  const callEvaluationStep = useCallback(async (
    userInput: string,
    context?: {
      job_title?: string
      seniority?: string
      department?: string
      location?: string
      work_model?: string
      technical_skills?: string[]
      behavioral_skills?: string[]
    }
  ): Promise<EvaluationStepResponse | null> => {
    setIsEvaluating(true)
    setError(null)

    try {
      const companyId = options.companyId || ''
      const response = await fetch(`/api/backend-proxy/lia/job-wizard/evaluate?company_id=${encodeURIComponent(companyId)}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          conversation_id: conversationId,
          user_input: userInput,
          context
        })
      })

      if (!response.ok) {
        throw new Error(`Evaluation error: ${response.status}`)
      }

      // Backend returns snake_case, need to transform
      const rawData = await response.json()
      
      // Map backend detected_fields to frontend detected_criteria
      const detectedFields = rawData.detected_fields || {}
      const mappedCriteria: DetectedCriteria = {
        job_title: detectedFields.title || detectedFields.job_title,
        seniority: detectedFields.seniority,
        department: detectedFields.department,
        manager: detectedFields.manager,
        manager_email: detectedFields.manager_email,
        recruiter: detectedFields.recruiter,
        recruiter_email: detectedFields.recruiter_email,
        responsibilities: detectedFields.responsibilities,
        technical_skills: detectedFields.technical_skills || detectedFields.skills?.technical,
        behavioral_skills: detectedFields.behavioral_skills || detectedFields.skills?.behavioral,
        salary_min: detectedFields.salary_min || detectedFields.salary?.min,
        salary_max: detectedFields.salary_max || detectedFields.salary?.max,
        work_model: detectedFields.work_model,
        location: detectedFields.location,
        employment_type: detectedFields.employment_type,
        deadline_screening: detectedFields.deadline_screening,
        deadline_shortlist: detectedFields.deadline_shortlist,
        deadline_closing: detectedFields.deadline_closing,
        deadline: detectedFields.deadline,
        is_confidential: detectedFields.is_confidential,
        visibility: detectedFields.visibility,
        whatsapp_template_type: detectedFields.whatsapp_template_type,
        pipeline_template_id: detectedFields.pipeline_template_id,
        is_affirmative: detectedFields.is_affirmative,
        affirmative_criteria_primary: detectedFields.affirmative_criteria_primary,
        affirmative_criteria_secondary: detectedFields.affirmative_criteria_secondary,
        affirmative_description: detectedFields.affirmative_description
      }
      
      // Build field origins from suggestions
      const fieldOrigins: Record<string, FieldOrigin> = {}
      const suggestions = rawData.suggestions || []
      for (const suggestion of suggestions) {
        if (suggestion.field) {
          fieldOrigins[suggestion.field] = {
            source: suggestion.source === 'market_benchmark' ? 'benchmark' : 
                    suggestion.source === 'company_policy' ? 'default' : 'detected',
            confidence: rawData.overall_confidence || 0.7,
            original_text: suggestion.reason
          }
        }
      }
      
      // Transform compensation analysis from backend format
      const transformedData: EvaluationStepResponse = {
        conversation_id: rawData.conversation_id,
        detected_criteria: mappedCriteria,
        field_origins: fieldOrigins,
        compensation_analysis: transformCompensationAnalysis(rawData.compensation_analysis),
        lia_message: rawData.lia_message,
        suggestions: rawData.suggestions
      }
      
      if (transformedData.conversation_id) {
        setConversationId(transformedData.conversation_id)
      }
      setEvaluationResult(transformedData)

      if (transformedData.detected_criteria && options.onCriteriaDetected) {
        options.onCriteriaDetected(
          transformedData.detected_criteria,
          transformedData.field_origins || {}
        )
      }

      return transformedData
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Unknown error')
      setError(error)
      options.onError?.(error)
      return null
    } finally {
      setIsEvaluating(false)
    }
  }, [conversationId, options])

  const clearEvaluationResult = useCallback(() => {
    setEvaluationResult(null)
  }, [])

  const fetchDeduplicatedSkills = useCallback(async (
    role: string,
    alreadySelectedSkills: string[] = [],
    seniority?: string
  ): Promise<DeduplicatedSkill[]> => {
    setIsFetchingSkills(true)
    setError(null)

    try {
      const companyId = options.companyId || ''
      const response = await fetch('/api/backend-proxy/lia/learning/skills-deduplicated', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          company_id: companyId,
          role,
          seniority,
          exclude_already_selected: alreadySelectedSkills
        })
      })

      if (!response.ok) {
        throw new Error(`Skills deduplication error: ${response.status}`)
      }

      const data: DeduplicatedSkillsResponse = await response.json()
      setDeduplicatedSkills(data.skills)
      return data.skills
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Unknown error')
      setError(error)
      options.onError?.(error)
      return []
    } finally {
      setIsFetchingSkills(false)
    }
  }, [options])

  const filterSkillSuggestions = useCallback((
    suggestions: string[],
    alreadySelected: string[]
  ): string[] => {
    const selectedLower = new Set(alreadySelected.map(s => s.toLowerCase().trim()))
    return suggestions.filter(s => !selectedLower.has(s.toLowerCase().trim()))
  }, [])

  const resetConversation = useCallback(() => {
    setConversationId(null)
    setLastResponse(null)
    setEvaluationResult(null)
    setDeduplicatedSkills([])
    setError(null)
  }, [])

  return {
    conversationId,
    isProcessing,
    isEvaluating,
    isFetchingSkills,
    lastResponse,
    evaluationResult,
    deduplicatedSkills,
    error,
    processStep,
    callEvaluationStep,
    fetchDeduplicatedSkills,
    filterSkillSuggestions,
    clearEvaluationResult,
    resetConversation
  }
}
