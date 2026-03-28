'use client'

import { useState, useCallback } from 'react'
import {
  orchestrateWizardMessage,
  type WizardOrchestratorRequest,
  type WizardOrchestratorResponse,
  type WizardOrchestratorAction,
} from '@/services/lia-api'
import type { WizardStage } from '../config'
import type {
  TechnicalSkill,
  BehavioralCompetency,
  SalaryInfo,
  BasicInfoFields,
  DetectedCriteria,
  OrchestratorFieldUpdates,
} from '../ExpandedChatContext'

export type { OrchestratorFieldUpdates }

export interface OrchestratorResult {
  action: WizardOrchestratorAction
  response: string
  fieldUpdates?: OrchestratorFieldUpdates
  targetStage?: WizardStage
  confidence: number
  reasoning?: string
  suggestions?: Array<{ field: string; value: any; reason: string }>
  validationErrors?: string[]
}

const BACKEND_TO_FRONTEND_FIELD_MAP: Record<string, string> = {
  salary_min: 'salaryInfo.minSalary',
  salary_max: 'salaryInfo.maxSalary',
  technical_skills: 'technicalSkills',
  behavioral_competencies: 'behavioralCompetencies',
  title: 'basicInfoFields.cargo',
  job_title: 'basicInfoFields.cargo',
  seniority_level: 'detectedCriteria.senioridadeIdiomas',
  work_model: 'basicInfoFields.modeloTrabalho',
  location: 'basicInfoFields.localidade',
  department: 'basicInfoFields.area',
  area: 'basicInfoFields.area',
  gestor: 'basicInfoFields.gestor',
  manager: 'basicInfoFields.gestor',
  contract_type: 'basicInfoFields.tipoContrato',
  tipo_contrato: 'basicInfoFields.tipoContrato',
  responsibilities: 'detectedCriteria.responsabilidades',
  languages: 'detectedCriteria.idiomas',
  experience: 'detectedCriteria.experienciaMinima',
  education: 'detectedCriteria.formacao',
  certifications: 'detectedCriteria.certificacoes',
  tools: 'detectedCriteria.ferramentas',
  benefits: 'detectedCriteria.beneficiosMencionados',
  bonus: 'detectedCriteria.bonus',
  is_affirmative: 'detectedCriteria.isAffirmative',
}

const BACKEND_TO_FRONTEND_STAGE_MAP: Record<string, WizardStage> = {
  // Numeric stage mappings from backend
  '1': 'input-evaluation',
  '2': 'salary',
  '3': 'competencies',
  '4': 'wsi-questions',
  '5': 'review-publish',
  '6': 'review-publish',
  '7': 'search-calibration',
  '8': 'search-calibration',
  // String stage mappings
  'input_evaluation': 'input-evaluation',
  'input-evaluation': 'input-evaluation',
  'assessment': 'input-evaluation',
  'salary': 'salary',
  'compensation': 'salary',
  'competencies': 'competencies',
  'skills': 'competencies',
  'wsi_questions': 'wsi-questions',
  'wsi-questions': 'wsi-questions',
  'screening': 'wsi-questions',
  // Review and publish stages
  'review': 'review-publish',
  'review-publish': 'review-publish',
  'summary': 'review-publish',
  'publish': 'review-publish',
  'pre-publish': 'review-publish',
  // Search and calibration stages
  'search': 'search-calibration',
  'search-calibration': 'search-calibration',
  'calibration': 'search-calibration',
  'candidate-search': 'search-calibration',
}

function mapBackendFieldsToFrontend(updates: Record<string, any>): OrchestratorFieldUpdates {
  const result: OrchestratorFieldUpdates = {
    salaryInfo: {},
    basicInfoFields: {},
    detectedCriteria: {},
  }

  for (const [backendKey, value] of Object.entries(updates)) {
    const frontendPath = BACKEND_TO_FRONTEND_FIELD_MAP[backendKey]
    
    if (!frontendPath) {
      console.warn(`Unknown backend field: ${backendKey}`)
      continue
    }

    const [category, field] = frontendPath.split('.')

    if (category === 'salaryInfo' && field) {
      const salaryValue = typeof value === 'number' ? String(value) : value
      result.salaryInfo = { ...result.salaryInfo, [field]: salaryValue }
    } else if (category === 'basicInfoFields' && field) {
      result.basicInfoFields = { ...result.basicInfoFields, [field]: value }
    } else if (category === 'detectedCriteria' && field) {
      result.detectedCriteria = { ...result.detectedCriteria, [field]: value }
    } else if (category === 'technicalSkills') {
      if (Array.isArray(value)) {
        result.technicalSkills = value.map((skill, index) => {
          if (typeof skill === 'string') {
            return {
              id: `skill-${Date.now()}-${index}`,
              name: skill,
              level: 'Intermediário' as const,
              required: true,
              category: 'tool' as const,
              weight: 3,
            }
          }
          return {
            id: skill.id || `skill-${Date.now()}-${index}`,
            name: skill.name || skill,
            level: skill.level || 'Intermediário',
            required: skill.required ?? true,
            category: skill.category || 'tool',
            weight: skill.weight || 3,
          }
        })
      }
    } else if (category === 'behavioralCompetencies') {
      if (Array.isArray(value)) {
        result.behavioralCompetencies = value.map((comp, index) => {
          if (typeof comp === 'string') {
            return {
              id: `comp-${Date.now()}-${index}`,
              name: comp,
              weight: 3,
              justification: '',
              enabled: true,
            }
          }
          return {
            id: comp.id || `comp-${Date.now()}-${index}`,
            name: comp.name || comp,
            weight: comp.weight || 3,
            justification: comp.justification || '',
            enabled: comp.enabled ?? true,
          }
        })
      }
    }
  }

  return result
}

function mapBackendStageToFrontend(stage: string | undefined): WizardStage | undefined {
  if (!stage) return undefined
  return BACKEND_TO_FRONTEND_STAGE_MAP[stage.toLowerCase()] || undefined
}

export interface UseWizardOrchestratorOptions {
  companyId?: string
}

export interface UseWizardOrchestratorReturn {
  isLoading: boolean
  error: string | null
  lastResult: OrchestratorResult | null
  sendMessage: (
    message: string,
    currentStage: WizardStage,
    collectedData: Record<string, any>,
    conversationHistory?: Array<{ role: string; content: string }>
  ) => Promise<OrchestratorResult>
  clearError: () => void
}

export function useWizardOrchestrator(
  options: UseWizardOrchestratorOptions = {}
): UseWizardOrchestratorReturn {
  const { companyId } = options
  
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastResult, setLastResult] = useState<OrchestratorResult | null>(null)

  const clearError = useCallback(() => {
    setError(null)
  }, [])

  const sendMessage = useCallback(
    async (
      message: string,
      currentStage: WizardStage,
      collectedData: Record<string, any>,
      conversationHistory?: Array<{ role: string; content: string }>
    ): Promise<OrchestratorResult> => {
      setIsLoading(true)
      setError(null)

      try {
        const request: WizardOrchestratorRequest = {
          message,
          current_stage: currentStage,
          collected_data: collectedData,
          conversation_history: conversationHistory,
          company_id: companyId,
        }

        const response: WizardOrchestratorResponse = await orchestrateWizardMessage(request)

        const result: OrchestratorResult = {
          action: response.action,
          response: response.response,
          confidence: response.confidence,
          reasoning: response.reasoning,
          suggestions: response.suggestions,
          validationErrors: response.validation_errors,
        }

        if (response.updated_fields) {
          result.fieldUpdates = mapBackendFieldsToFrontend(response.updated_fields)
        }

        if (response.target_stage) {
          result.targetStage = mapBackendStageToFrontend(response.target_stage)
        }

        setLastResult(result)
        return result
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Erro ao processar mensagem'
        setError(errorMessage)
        
        const fallbackResult: OrchestratorResult = {
          action: 'respond',
          response: 'Desculpe, tive um problema ao processar sua mensagem. Pode tentar novamente?',
          confidence: 0.3,
        }
        setLastResult(fallbackResult)
        return fallbackResult
      } finally {
        setIsLoading(false)
      }
    },
    [companyId]
  )

  return {
    isLoading,
    error,
    lastResult,
    sendMessage,
    clearError,
  }
}
