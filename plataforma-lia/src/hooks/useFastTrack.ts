/**
 * useFastTrack hook - Detects similar jobs and enables Fast Track job creation
 * 
 * Philosophy: "Copia tudo, pergunta uma vez"
 * - Conversational interface (LIA asks, user responds naturally)
 * - Copy all fields from previous job
 * - Ask only for sensitive fields (affirmative, manager, location)
 * - Regenerate WSI questions if competencies change
 */
import { useState, useCallback, useEffect, useRef } from 'react'
import type { 
  TechnicalSkill, 
  BehavioralCompetency, 
  Benefit, 
  WSIQuestion,
  BasicInfoFields,
  SalaryInfo,
  DetectedCriteria
} from '@/components/expanded-chat/ExpandedChatContext'

export interface FastTrackSuggestion {
  job_id: string
  job_title: string
  department?: string
  seniority?: string
  location?: string
  work_model?: string
  similarity_score: number
  outcome_status?: string
  time_to_fill_days?: number
  created_at?: string
  skills?: string[]
  technical_skills?: string[]
  behavioral_competencies?: Array<{ name: string; weight?: number } | string>
  salary_min?: number
  salary_max?: number
  benefits?: Array<{ id?: string; name: string; value?: string; enabled?: boolean } | string>
  wsi_questions?: WSIQuestion[]
  description?: string
  responsibilities?: string[]
  requirements?: string
  gestor?: string
  manager?: string
  manager_email?: string
  employment_type?: string
  is_affirmative?: boolean
  affirmative_criteria_primary?: string
  affirmative_criteria_secondary?: string
  languages?: string[]
}

export interface FastTrackJobData {
  basicInfo: Partial<BasicInfoFields>
  technicalSkills: TechnicalSkill[]
  behavioralCompetencies: BehavioralCompetency[]
  salaryInfo: Partial<SalaryInfo>
  wsiQuestions: WSIQuestion[]
  detectedCriteria: Partial<DetectedCriteria>
  generatedDescription?: string
  sourceJobId: string
  sourceJobTitle: string
}

export interface FastTrackState {
  suggestions: FastTrackSuggestion[]
  isLoading: boolean
  isApplying: boolean
  error: string | null
  hasSuggestions: boolean
  selectedJob: FastTrackSuggestion | null
  isFastTrackMode: boolean
  appliedFromJobId: string | null
}

interface FastTrackOptions {
  companyId: string
  debounceMs?: number
  minTitleLength?: number
  minSimilarity?: number
}

const BACKEND_URL = '/api/backend-proxy'

export function useFastTrack(options: FastTrackOptions) {
  const { 
    companyId, 
    debounceMs = 500, 
    minTitleLength = 3,
    minSimilarity = 0.70 
  } = options
  
  const [state, setState] = useState<FastTrackState>({
    suggestions: [],
    isLoading: false,
    isApplying: false,
    error: null,
    hasSuggestions: false,
    selectedJob: null,
    isFastTrackMode: false,
    appliedFromJobId: null,
  })
  
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null)
  const abortControllerRef = useRef<AbortController | null>(null)
  const lastSearchedTitleRef = useRef<string>('')
  
  const searchSimilarJobs = useCallback(async (jobTitle: string, department?: string) => {
    if (jobTitle.length < minTitleLength) {
      setState(prev => ({ 
        ...prev, 
        suggestions: [], 
        hasSuggestions: false, 
        isLoading: false 
      }))
      return []
    }
    
    const searchKey = `${jobTitle}_${department || ''}`
    if (searchKey === lastSearchedTitleRef.current) {
      return state.suggestions
    }
    
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    
    abortControllerRef.current = new AbortController()
    
    setState(prev => ({ ...prev, isLoading: true, error: null }))
    
    try {
      const response = await fetch(`${BACKEND_URL}/job-embeddings/fast-track`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          company_id: companyId,
          job_title: jobTitle,
          department,
          limit: 5,
        }),
        signal: abortControllerRef.current.signal,
      })
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }
      
      const data = await response.json()
      const suggestions = (data.suggestions || []).filter(
        (s: FastTrackSuggestion) => s.similarity_score >= minSimilarity
      )
      
      lastSearchedTitleRef.current = searchKey
      
      setState(prev => ({
        ...prev,
        suggestions,
        hasSuggestions: suggestions.length > 0,
        isLoading: false,
      }))
      
      return suggestions
      
    } catch (error) {
      if ((error as Error).name === 'AbortError') {
        return []
      }
      
      const errorMessage = (error as Error).message || 'Erro ao buscar vagas similares'
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: errorMessage,
        suggestions: [],
        hasSuggestions: false,
      }))
      
      return []
    }
  }, [companyId, minSimilarity, minTitleLength, state.suggestions])
  
  const searchWithDebounce = useCallback((jobTitle: string, department?: string) => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current)
    }
    
    debounceTimerRef.current = setTimeout(() => {
      searchSimilarJobs(jobTitle, department)
    }, debounceMs)
  }, [debounceMs, searchSimilarJobs])
  
  const selectJob = useCallback((job: FastTrackSuggestion) => {
    setState(prev => ({ ...prev, selectedJob: job }))
  }, [])
  
  const clearSelection = useCallback(() => {
    setState(prev => ({ ...prev, selectedJob: null }))
  }, [])
  
  const applyFastTrack = useCallback(async (
    job: FastTrackSuggestion
  ): Promise<FastTrackJobData | null> => {
    setState(prev => ({ ...prev, isApplying: true, error: null }))
    
    try {
      const skillsList = job.technical_skills || job.skills || []
      const technicalSkills: TechnicalSkill[] = skillsList.map((skill, index) => {
        let skillName = ''
        if (typeof skill === 'string') {
          skillName = skill
        } else if (skill && typeof skill === 'object') {
          skillName = (skill as any).name || (skill as any).technology || String(skill)
        } else {
          skillName = String(skill)
        }
        return {
          id: `ft-skill-${index}-${Date.now()}`,
          name: skillName,
          level: 'Intermediário' as const,
          required: index < 3,
          category: 'tool' as const,
          weight: 3,
        }
      })
      
      const behavioralList = job.behavioral_competencies || []
      const behavioralCompetencies: BehavioralCompetency[] = behavioralList.map((comp, index) => {
        if (typeof comp === 'string') {
          return {
            id: `ft-behavioral-${index}-${Date.now()}`,
            name: comp,
            weight: 4,
            justification: 'Copiado da vaga anterior',
            enabled: true,
          }
        }
        return {
          id: `ft-behavioral-${index}-${Date.now()}`,
          name: comp.name,
          weight: comp.weight || 4,
          justification: 'Copiado da vaga anterior',
          enabled: true,
        }
      })
      
      const defaultBenefits: Benefit[] = [
        { id: '1', name: 'Vale Refeição', value: 'R$ 35/dia', enabled: true },
        { id: '2', name: 'Vale Transporte', enabled: true },
        { id: '3', name: 'Plano de Saúde', enabled: true },
        { id: '4', name: 'Plano Odontológico', enabled: true },
        { id: '5', name: 'Seguro de Vida', enabled: true },
      ]
      
      let benefits: Benefit[] = defaultBenefits
      if (job.benefits && job.benefits.length > 0) {
        benefits = job.benefits.map((b, index) => {
          if (typeof b === 'string') {
            return { id: String(index + 1), name: b, enabled: true }
          }
          return {
            id: b.id || String(index + 1),
            name: b.name,
            value: b.value,
            enabled: b.enabled !== false,
          }
        })
      }
      
      const wsiQuestions: WSIQuestion[] = (job.wsi_questions || []).map((q, index) => ({
        id: q.id || `ft-wsi-${index}-${Date.now()}`,
        question: q.question,
        type: q.type || 'open',
        required: q.required !== false,
        options: q.options,
        competencyValidated: (q as any).competency_validated || q.competencyValidated,
      }))
      
      const gestorName = job.manager || job.gestor || ''
      const skillNamesForCriteria = skillsList.map(s => {
        if (typeof s === 'string') return s
        if (s && typeof s === 'object') return (s as any).name || (s as any).technology || String(s)
        return String(s)
      })
      const behavioralNamesForCriteria = behavioralList.map(c => typeof c === 'string' ? c : c.name)
      
      const fastTrackData: FastTrackJobData = {
        basicInfo: {
          cargo: job.job_title,
          area: job.department || '',
          gestor: gestorName,
          localidade: job.location || '',
          modeloTrabalho: job.work_model || 'Híbrido',
          tipoContrato: job.employment_type || 'CLT',
        },
        technicalSkills,
        behavioralCompetencies,
        salaryInfo: {
          minSalary: job.salary_min ? job.salary_min.toString() : '',
          maxSalary: job.salary_max ? job.salary_max.toString() : '',
          minBonus: '',
          maxBonus: '',
          bonusCriteria: '',
          benefits,
        },
        wsiQuestions,
        detectedCriteria: {
          cargo: job.job_title,
          gestorArea: gestorName || null,
          responsabilidades: job.responsibilities || [],
          competenciasTecnicas: skillNamesForCriteria,
          competenciasComportamentais: behavioralNamesForCriteria,
          senioridadeIdiomas: job.seniority || null,
          modeloTrabalho: job.work_model || null,
          localizacao: job.location || null,
          departamento: job.department || null,
          isAffirmative: job.is_affirmative || null,
          affirmativeCriteriaPrimary: job.affirmative_criteria_primary || null,
          affirmativeCriteriaSecondary: job.affirmative_criteria_secondary || null,
        },
        generatedDescription: job.description,
        sourceJobId: job.job_id,
        sourceJobTitle: job.job_title,
      }
      
      setState(prev => ({
        ...prev,
        isApplying: false,
        isFastTrackMode: true,
        appliedFromJobId: job.job_id,
        selectedJob: job,
      }))
      
      return fastTrackData
      
    } catch (error) {
      const errorMessage = (error as Error).message || 'Erro ao aplicar Fast Track'
      setState(prev => ({
        ...prev,
        isApplying: false,
        error: errorMessage,
      }))
      
      return null
    }
  }, [])
  
  const exitFastTrackMode = useCallback(() => {
    setState(prev => ({
      ...prev,
      isFastTrackMode: false,
      appliedFromJobId: null,
      selectedJob: null,
    }))
  }, [])
  
  const clearSuggestions = useCallback(() => {
    lastSearchedTitleRef.current = ''
    setState({
      suggestions: [],
      isLoading: false,
      isApplying: false,
      error: null,
      hasSuggestions: false,
      selectedJob: null,
      isFastTrackMode: false,
      appliedFromJobId: null,
    })
  }, [])
  
  const getLiaMessage = useCallback((suggestions: FastTrackSuggestion[]): string => {
    if (suggestions.length === 0) {
      return ''
    }
    
    const topSuggestion = suggestions[0]
    const timeInfo = topSuggestion.time_to_fill_days 
      ? `Foi um sucesso - contratamos em ${topSuggestion.time_to_fill_days} dias!`
      : ''
    
    const dateInfo = topSuggestion.created_at
      ? new Date(topSuggestion.created_at).toLocaleDateString('pt-BR', { month: 'short', year: 'numeric' })
      : ''
    
    if (suggestions.length === 1) {
      return `Encontrei uma vaga similar! "${topSuggestion.job_title}"${topSuggestion.department ? ` do time ${topSuggestion.department}` : ''}${dateInfo ? `, criada em ${dateInfo}` : ''}. ${timeInfo}

Quer usar ela como base? Vai economizar bastante tempo!`
    }
    
    return `Encontrei ${suggestions.length} vagas similares! A mais recente foi "${topSuggestion.job_title}"${topSuggestion.department ? ` do time ${topSuggestion.department}` : ''}${dateInfo ? `, criada em ${dateInfo}` : ''}. ${timeInfo}

Quer usar uma delas como base? Vai ser bem mais rápido!`
  }, [])
  
  const getConfirmationMessage = useCallback((job: FastTrackSuggestion): string => {
    const skillsList = job.technical_skills || job.skills || []
    const skillsCount = skillsList.length
    const behavioralList = job.behavioral_competencies || []
    const behavioralCount = behavioralList.length
    const salaryInfo = job.salary_min && job.salary_max
      ? `R$ ${(job.salary_min / 1000).toFixed(0)}k - ${(job.salary_max / 1000).toFixed(0)}k`
      : ''
    const wsiCount = job.wsi_questions?.length || 0
    const gestorName = job.manager || job.gestor
    
    return `Copiei tudo da vaga anterior:

• ${skillsCount} skills técnicas
• ${behavioralCount} competências comportamentais
• Salário: ${salaryInfo || 'a definir'}
• ${wsiCount} perguntas WSI de triagem

Só preciso confirmar alguns dados:

1. Quem é o gestor desta vaga?${gestorName ? ` (anterior: ${gestorName})` : ''}
2. A localização continua ${job.location || 'a mesma'}?
3. Essa vaga é afirmativa?`
  }, [])
  
  const recordFastTrackUsage = useCallback(async (
    newJobId: string,
    modifiedFields: string[],
    wasPublished: boolean
  ): Promise<void> => {
    if (!state.appliedFromJobId) return
    
    try {
      await fetch(`${BACKEND_URL}/job-embeddings/fast-track/record-usage`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          company_id: companyId,
          source_job_id: state.appliedFromJobId,
          new_job_id: newJobId,
          modified_fields: modifiedFields,
          was_published: wasPublished
        })
      })
    } catch (error) {
    }
  }, [companyId, state.appliedFromJobId])
  
  useEffect(() => {
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current)
      }
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
    }
  }, [])
  
  return {
    ...state,
    searchSimilarJobs,
    searchWithDebounce,
    selectJob,
    clearSelection,
    applyFastTrack,
    exitFastTrackMode,
    clearSuggestions,
    getLiaMessage,
    getConfirmationMessage,
    recordFastTrackUsage,
  }
}

export type { FastTrackOptions }
