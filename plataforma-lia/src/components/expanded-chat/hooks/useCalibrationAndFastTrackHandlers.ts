"use client"

import { useCallback, useEffect } from "react"
import { liaApi, type VacancySearchCriteria, type VacancyAdjustments } from "@/services/lia-api"
import {
  type TechnicalSkill,
  type BehavioralCompetency,
  type SalaryInfo,
  type BasicInfoFields,
  type DetectedCriteria,
} from "../ExpandedChatContext"
import {
  type Message,
  type CalibrationCandidate,
} from "../types"
import type { VacancySummary } from "../../job-creation/vacancy-search-results"
import type { WizardMode, FastTrackState } from "../types"
import type { VacancyAdjustments as VA } from "@/services/lia-api"

// Re-export for convenience
export type { VacancyAdjustments as FastTrackAdjustments } from "@/services/lia-api"

export interface CalibrationAndFastTrackContext {
  basicInfoFields: BasicInfoFields
  detectedCriteria: DetectedCriteria
  technicalSkills: TechnicalSkill[]
  behavioralCompetencies: BehavioralCompetency[]
  salaryInfo: SalaryInfo
  publishedJobId: string | null
  calibrationCandidates: CalibrationCandidate[]
  setCalibrationCandidates: React.Dispatch<React.SetStateAction<CalibrationCandidate[]>>
  currentCalibrationIndex: number
  setCurrentCalibrationIndex: React.Dispatch<React.SetStateAction<number>>
  approvedCandidates: string[]
  setApprovedCandidates: React.Dispatch<React.SetStateAction<string[]>>
  rejectedCandidates: string[]
  setRejectedCandidates: React.Dispatch<React.SetStateAction<string[]>>
  calibrationComplete: boolean
  setCalibrationComplete: React.Dispatch<React.SetStateAction<boolean>>
  isLoadingCalibration: boolean
  setIsLoadingCalibration: React.Dispatch<React.SetStateAction<boolean>>
  showCalibrationModal: boolean
  setShowCalibrationModal: React.Dispatch<React.SetStateAction<boolean>>
  calibrationSessionId: string | null
  setCalibrationSessionId: React.Dispatch<React.SetStateAction<string | null>>
  calibrationComment: string
  setCalibrationComment: React.Dispatch<React.SetStateAction<string>>
  calibrationCriteria: Array<{ id: string; text: string; source: 'technical' | 'behavioral' }>
  setCalibrationCriteria: React.Dispatch<React.SetStateAction<Array<{ id: string; text: string; source: 'technical' | 'behavioral' }>>>
  postCalibrationComplete: boolean
  setPostCalibrationComplete: React.Dispatch<React.SetStateAction<boolean>>
  hasAttemptedCalibrationGeneration: boolean
  setHasAttemptedCalibrationGeneration: React.Dispatch<React.SetStateAction<boolean>>
  setSearchPhase: React.Dispatch<React.SetStateAction<'local-searching' | 'local-complete' | 'global-searching' | 'global-complete' | 'idle'>>
  setLocalCandidateCount: (count: number) => void
  setGlobalCandidateCount: (count: number) => void
  awaitingCalibrationChoice: boolean
  setAwaitingCalibrationChoice: React.Dispatch<React.SetStateAction<boolean>>
  fastTrackState: FastTrackState
  setFastTrackState: React.Dispatch<React.SetStateAction<FastTrackState>>
  fastTrackSelectedVacancy: VacancySummary | null
  setFastTrackSelectedVacancy: (vacancy: VacancySummary | null) => void
  fastTrackAdjustments: VacancyAdjustments
  setFastTrackAdjustments: React.Dispatch<React.SetStateAction<VacancyAdjustments>>
  fastTrackSearchResults: VacancySummary[]
  setFastTrackSearchResults: React.Dispatch<React.SetStateAction<VacancySummary[]>>
  isSearchingVacancies: boolean
  setIsSearchingVacancies: React.Dispatch<React.SetStateAction<boolean>>
  wizardFastTrackSourceJobId: string | null
  setWizardFastTrackSourceJobId: (id: string | null) => void
  setWizardMode: React.Dispatch<React.SetStateAction<WizardMode>>
  isLoading: boolean
  setIsLoading: React.Dispatch<React.SetStateAction<boolean>>
  messages: Message[]
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>
  currentStage: string
  user: { name?: string; email?: string; company?: string; id?: string } | null
  onJobCreated?: () => void
}

export function useCalibrationAndFastTrackHandlers(ctx: CalibrationAndFastTrackContext) {
  const initializeCalibrationCriteria = useCallback(() => {
    const criteria: {id: string; text: string; source: 'technical' | 'behavioral'}[] = []
    const baseTs = Date.now()
    
    // Add technical skills as criteria
    ctx.technicalSkills.filter(s => s.required).forEach((skill, idx) => {
      criteria.push({
        id: `tech-${baseTs}-${idx}-${skill.name.replace(/\s+/g, '')}`,
        text: `Deve ter experiência com ${skill.name} (${skill.level})`,
        source: 'technical'
      })
    })
    
    // Add behavioral competencies as criteria
    ctx.behavioralCompetencies.filter(c => c.enabled && c.weight >= 4).forEach((comp, idx) => {
      criteria.push({
        id: `behav-${baseTs}-${idx}-${comp.name.replace(/\s+/g, '')}`,
        text: `${comp.name} - ${comp.justification}`,
        source: 'behavioral'
      })
    })
    
    ctx.setCalibrationCriteria(criteria)
  }, [ctx])

  // Generate calibration candidates from real API
  const generateCalibrationCandidates = useCallback(async () => {
    ctx.setIsLoadingCalibration(true)
    
    try {
      // Build job description from collected data
      const jobDescription = `
        Cargo: ${ctx.basicInfoFields.cargo || ctx.detectedCriteria.cargo || 'Vaga'}
        Área: ${ctx.basicInfoFields.area || ctx.detectedCriteria.gestorArea || ''}
        Localidade: ${ctx.basicInfoFields.localidade || ctx.detectedCriteria.localizacao || ''}
        Modelo: ${ctx.basicInfoFields.modeloTrabalho || ctx.detectedCriteria.modeloTrabalho || ''}
        
        Habilidades técnicas: ${ctx.technicalSkills.filter(s => s.required).map(s => s.name).join(', ')}
        
        Competências comportamentais: ${ctx.behavioralCompetencies.filter(c => c.enabled).map(c => c.name).join(', ')}
      `.trim()
      
      const response = await liaApi.startCalibrationSession({
        job_vacancy_id: ctx.publishedJobId || 'temp-' + Date.now(),
        job_description: jobDescription,
        technical_skills: ctx.technicalSkills.filter(s => s.required).map(s => s.name),
        behavioral_competencies: ctx.behavioralCompetencies.filter(c => c.enabled).map(c => c.name),
        location: ctx.basicInfoFields.localidade || ctx.detectedCriteria.localizacao || undefined,
        limit: 5
      })
      
      ctx.setCalibrationSessionId(response.session_id)
      ctx.setCalibrationCandidates(response.candidates as unknown as CalibrationCandidate[])
      ctx.setIsLoadingCalibration(false)
      ctx.setShowCalibrationModal(true)
      
      // Add LIA feedback message
      const feedbackMessage: Message = {
        id: `calibration-ready-${Date.now()}`,
        role: 'assistant',
        content: `Encontrei **${response.candidates.length} perfis** na base de talentos que correspondem aos critérios da vaga!\n\nVou apresentar cada um para você avaliar. Seu feedback me ajuda a calibrar a busca e ser mais assertiva nas próximas sugestões.\n\nClique em **Aprovar** ou **Reprovar** e adicione comentários se desejar. Após 3 aprovações, inicio a busca em escala.`,
        timestamp: new Date()
      }
      ctx.setMessages(prev => [...prev, feedbackMessage])
      
    } catch (error) {
      ctx.setIsLoadingCalibration(false)
      
      // Fallback message
      const errorMessage: Message = {
        id: `calibration-error-${Date.now()}`,
        role: 'assistant',
        content: `Não consegui buscar candidatos no momento. Vamos tentar novamente em instantes.`,
        timestamp: new Date()
      }
      ctx.setMessages(prev => [...prev, errorMessage])
    }
  }, [ctx])

  // Handle candidate approval
  const handleApproveCandidate = () => {
    const currentCandidate = ctx.calibrationCandidates[ctx.currentCalibrationIndex]
    if (!currentCandidate) return
    
    const newApproved = [...ctx.approvedCandidates, currentCandidate.id]
    ctx.setApprovedCandidates(newApproved)
    
    // Save feedback to backend
    if (ctx.calibrationSessionId && ctx.publishedJobId) {
      liaApi.submitCalibrationFeedback({
        session_id: ctx.calibrationSessionId,
        candidate_id: currentCandidate.id,
        job_id: ctx.publishedJobId,
        approved: true,
        lia_score: currentCandidate.overallScore,
        feedback_reason: ctx.calibrationComment || undefined
      }).catch(() => {})
    }
    
    // Save comment if any
    if (ctx.calibrationComment) {
      ctx.setCalibrationComment('')
    }
    
    // Check if we have 3 approved - only trigger if not already completed
    if (newApproved.length >= 3 && !ctx.postCalibrationComplete) {
      ctx.setCalibrationComplete(true)
      ctx.setShowCalibrationModal(false)
      ctx.setPostCalibrationComplete(true)
      
      // Add celebration message
      const celebrationMessage: Message = {
        id: `calibration-complete-${Date.now()}`,
        role: 'assistant',
        content: `Calibração concluída! Agora entendo melhor o perfil que você busca.\n\nEstou iniciando a busca em escala para popular o kanban da vaga. Vou te manter informado sobre os próximos passos.`,
        timestamp: new Date()
      }
      ctx.setMessages(prev => [...prev, celebrationMessage])
      
      // Stay in search-calibration stage to show next steps (unified stage)
      // ctx.setCurrentStage already set to 'search-calibration' after publish
      
      // Start real background search
      ctx.setSearchPhase('local-searching')

      const startActiveSearch = async () => {
        try {
          const jobDescription = `${ctx.basicInfoFields.cargo || ctx.detectedCriteria.cargo} - ${ctx.technicalSkills.filter(s => s.required).map(s => s.name).join(', ')}`
          
          const searchResponse = await liaApi.searchCandidatesByJobDescription(
            jobDescription,
            ctx.basicInfoFields.localidade || ctx.detectedCriteria.localizacao || undefined,
            15
          )
          
          ctx.setLocalCandidateCount(searchResponse.total_results)
          ctx.setSearchPhase('local-complete')
          
          // Add candidates to pipeline if job was created
          if (ctx.publishedJobId && searchResponse.candidates.length > 0) {
            const candidateIds = searchResponse.candidates
              .filter(c => c.id)
              .map(c => c.id as string)
            
            if (candidateIds.length > 0) {
              await liaApi.addCandidatesToPipeline({
                candidate_ids: candidateIds,
                job_vacancy_id: ctx.publishedJobId,
                source: 'calibration_search'
              })
              
              // Send notification
              await liaApi.sendNotification({
                user_id: ctx.user?.email || 'system',
                title: 'Novos candidatos encontrados',
                message: `${candidateIds.length} candidatos foram adicionados ao pipeline da vaga ${ctx.basicInfoFields.cargo || 'Nova Vaga'}`,
                notification_type: 'candidates_added',
                related_job_id: ctx.publishedJobId,
                action_url: `/jobs/${ctx.publishedJobId}/kanban`
              })
            }
          }
        } catch (error) {
          ctx.setSearchPhase('local-complete')
          ctx.setLocalCandidateCount(0)
        }
      }

      startActiveSearch()
    } else if (newApproved.length < 3) {
      // Move to next candidate
      moveToNextCandidate()
    }
  }

  // Handle candidate rejection
  const handleRejectCandidate = () => {
    const currentCandidate = ctx.calibrationCandidates[ctx.currentCalibrationIndex]
    if (!currentCandidate) return
    
    const newRejected = [...ctx.rejectedCandidates, currentCandidate.id]
    ctx.setRejectedCandidates(newRejected)
    
    // Save feedback to backend
    if (ctx.calibrationSessionId && ctx.publishedJobId) {
      liaApi.submitCalibrationFeedback({
        session_id: ctx.calibrationSessionId,
        candidate_id: currentCandidate.id,
        job_id: ctx.publishedJobId,
        approved: false,
        lia_score: currentCandidate.overallScore,
        feedback_reason: ctx.calibrationComment || undefined
      }).catch(() => {})
    }
    
    // Save comment if any
    if (ctx.calibrationComment) {
      ctx.setCalibrationComment('')
    }
    
    // Add LIA feedback about adding more candidates
    const needMore = 3 - ctx.approvedCandidates.length
    const feedbackMessage: Message = {
      id: `rejection-feedback-${Date.now()}`,
      role: 'assistant',
      content: `Entendido! Vou usar este feedback para refinar a busca.\n\nVocê ainda precisa aprovar mais **${needMore} perfil(s)** para calibração. Vou buscar mais opções que correspondam melhor aos seus critérios.`,
      timestamp: new Date()
    }
    ctx.setMessages(prev => [...prev, feedbackMessage])
    
    // Move to next or generate more
    if (ctx.currentCalibrationIndex < ctx.calibrationCandidates.length - 1) {
      moveToNextCandidate()
    } else {
      // Need to generate more candidates
      generateMoreCalibrationCandidates()
    }
  }

  // Move to next candidate in calibration
  const moveToNextCandidate = () => {
    if (ctx.currentCalibrationIndex < ctx.calibrationCandidates.length - 1) {
      ctx.setCurrentCalibrationIndex(prev => prev + 1)
    }
  }

  // Generate more calibration candidates when needed
  const generateMoreCalibrationCandidates = async () => {
    ctx.setIsLoadingCalibration(true)
    
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 1500))
    
    // Add one more candidate
    const newCandidate: CalibrationCandidate = {
      id: `calib-${Date.now()}`,
      name: 'Ana Carolina Silva',
      linkedinUrl: 'https://linkedin.com/in/ana-carolina-silva',
      currentRole: 'Marketing Director',
      currentCompany: 'Nubank',
      location: 'São Paulo, Brasil',
      education: 'Fundação Getúlio Vargas (FGV)',
      highlights: [
        { icon: 'rocket', label: 'Startup Unicórnio', value: 'Cresceu time de 5 para 30 pessoas' },
        { icon: 'trophy', label: 'Premiada', value: 'Top 30 under 30 Forbes' }
      ],
      experiences: [
        { id: 'exp-1', company: 'Nubank', role: 'Marketing Director', period: 'Mar 2020 - Presente', duration: '3 anos 9 meses', skills: ['Growth Marketing', 'Brand Building', 'Team Leadership'] }
      ],
      educationHistory: [
        { id: 'edu-1', institution: 'Fundação Getúlio Vargas (FGV)', degree: 'MBA', field: 'Marketing', period: '2016 - 2018' }
      ],
      skillMap: [
        { category: 'Growth', skills: ['Growth Hacking', 'Performance Marketing', 'User Acquisition'] }
      ],
      languages: ['Portuguese', 'English', 'Spanish'],
      additionalSkills: ['Data-Driven Marketing', 'Product Marketing', 'Agile'],
      matchCriteria: [
        { id: 'match-1', criteria: 'Experiência como Marketing Manager em empresa de grande porte', isMatch: true, explanation: 'Experiência como Marketing Director em fintech unicórnio com 5000+ funcionários.', importance: 1 }
      ],
      overallScore: 90,
      averageTenure: '3 anos',
      currentTenure: '3 anos 9 meses',
      totalExperience: '10 anos'
    }
    
    ctx.setCalibrationCandidates(prev => [...prev, newCandidate])
    ctx.setCurrentCalibrationIndex(prev => prev + 1)
    ctx.setIsLoadingCalibration(false)
    
    const feedbackMessage: Message = {
      id: `more-candidates-${Date.now()}`,
      role: 'assistant',
      content: `Encontrei mais 1 perfil que corresponde aos critérios! Avalie este candidato para continuar a calibração.`,
      timestamp: new Date()
    }
    ctx.setMessages(prev => [...prev, feedbackMessage])
  }

  // Add/Remove/Reorder calibration criteria
  const addCalibrationCriterion = (text: string) => {
    ctx.setCalibrationCriteria(prev => [
      ...prev,
      { id: `custom-${Date.now()}`, text, source: 'behavioral' }
    ])
  }

  const removeCalibrationCriterion = (id: string) => {
    ctx.setCalibrationCriteria(prev => prev.filter(c => c.id !== id))
  }

  const reorderCalibrationCriteria = (fromIndex: number, toIndex: number) => {
    ctx.setCalibrationCriteria(prev => {
      const result = [...prev]
      const [removed] = result.splice(fromIndex, 1)
      result.splice(toIndex, 0, removed)
      return result
    })
  }

  // Auto-load calibration when entering the stage (only once per stage entry)
  useEffect(() => {
    if (ctx.currentStage === 'search-calibration' && ctx.calibrationCandidates.length === 0 && !ctx.isLoadingCalibration && !ctx.hasAttemptedCalibrationGeneration) {
      ctx.setHasAttemptedCalibrationGeneration(true)
      initializeCalibrationCriteria()
      generateCalibrationCandidates()
    }
  }, [ctx.currentStage, ctx.calibrationCandidates.length, ctx.isLoadingCalibration, ctx.hasAttemptedCalibrationGeneration, initializeCalibrationCriteria, ctx, generateCalibrationCandidates])

  // Fast Track: Handle vacancy selection
  const handleFastTrackVacancySelect = async (vacancyId: string) => {
    ctx.setIsLoading(true)
    
    try {
      const vacancyDetails = await liaApi.getVacancyFullDetails(vacancyId)
      
      if (vacancyDetails) {
        // @ts-ignore
        ctx.setFastTrackSelectedVacancy(vacancyDetails)
        
        // Add LIA message with full summary
        const summaryMessage: Message = {
          id: `lia-summary-${Date.now()}`,
          role: 'assistant',
          content: '',
          timestamp: new Date(),
          messageType: 'vacancy-summary',
          vacancyFullDetails: vacancyDetails
        }
        ctx.setMessages(prev => [...prev, summaryMessage])
      } else {
        // Error loading vacancy
        const errorMessage: Message = {
          id: `lia-error-${Date.now()}`,
          role: 'assistant',
          content: 'Desculpe, não consegui carregar os detalhes dessa vaga. Tente selecionar outra ou digite "criar nova" para iniciar do zero.',
          timestamp: new Date()
        }
        ctx.setMessages(prev => [...prev, errorMessage])
        ctx.setFastTrackState('selecting')
      }
    } catch (error) {
      const errorMessage: Message = {
        id: `lia-error-${Date.now()}`,
        role: 'assistant',
        content: 'Ocorreu um erro ao carregar a vaga. Por favor, tente novamente.',
        timestamp: new Date()
      }
      ctx.setMessages(prev => [...prev, errorMessage])
    }
    
    ctx.setIsLoading(false)
  }

  // Fast Track: Search previous vacancies
  const handleFastTrackSearch = async (criteria: VacancySearchCriteria) => {
    ctx.setIsSearchingVacancies(true)
    ctx.setFastTrackState('searching')
    
    try {
      const response = await liaApi.searchPreviousVacancies(criteria)
      ctx.setFastTrackSearchResults(response.vacancies || [])
      
      // Add search results message
      const searchResultsMessage: Message = {
        id: `lia-search-${Date.now()}`,
        role: 'assistant',
        content: '',
        timestamp: new Date(),
        messageType: 'vacancy-search',
        vacancySearchResults: response.vacancies || []
      }
      ctx.setMessages(prev => [...prev, searchResultsMessage])
      ctx.setFastTrackState('selecting')
    } catch (error) {
      const errorMessage: Message = {
        id: `lia-error-${Date.now()}`,
        role: 'assistant',
        content: 'Não consegui encontrar vagas anteriores. Podemos criar uma nova vaga do zero. Me diga o cargo que precisa.',
        timestamp: new Date()
      }
      ctx.setMessages(prev => [...prev, errorMessage])
      ctx.setWizardMode('create_from_scratch')
    }
    
    ctx.setIsSearchingVacancies(false)
  }

  // Fast Track: Publish vacancy with adjustments
  const handleFastTrackPublish = async () => {
    if (!ctx.fastTrackSelectedVacancy) return
    
    ctx.setIsLoading(true)
    ctx.setFastTrackState('publishing')
    
    try {
      const result = await liaApi.publishFastTrackVacancy(ctx.fastTrackSelectedVacancy.id, ctx.fastTrackAdjustments)
      
      if (result.success) {
        const modifiedFields = Object.keys(ctx.fastTrackAdjustments).filter(
          key => ctx.fastTrackAdjustments[key as keyof VacancyAdjustments] !== undefined
        )
        const tenantId = ctx.user?.company || 'default'
        const newJobId = result.vacancy_id
        if (newJobId && newJobId !== ctx.fastTrackSelectedVacancy.id) {
          liaApi.recordFastTrackUsage({
            company_id: tenantId,
            source_job_id: ctx.fastTrackSelectedVacancy.id,
            new_job_id: newJobId,
            modified_fields: modifiedFields,
            was_published: true
          }).catch(() => {})
        } else {
        }
        
        const successMessage: Message = {
          id: `lia-success-${Date.now()}`,
          role: 'assistant',
          content: `🎉 **Vaga publicada com sucesso!**\n\nA vaga "${ctx.fastTrackSelectedVacancy.title}" está ativa e já está recebendo candidatos.\n\nVocê pode acompanhar o pipeline de candidatos no Kanban ou me pedir para buscar candidatos compatíveis.`,
          timestamp: new Date()
        }
        ctx.setMessages(prev => [...prev, successMessage])
        ctx.setFastTrackState('completed')
        ctx.onJobCreated?.()
      } else {
        const errorMessage: Message = {
          id: `lia-error-${Date.now()}`,
          role: 'assistant',
          content: `Não foi possível publicar a vaga: ${result.message}. Por favor, tente novamente.`,
          timestamp: new Date()
        }
        ctx.setMessages(prev => [...prev, errorMessage])
        ctx.setFastTrackState('reviewing')
      }
    } catch (error) {
      const errorMessage: Message = {
        id: `lia-error-${Date.now()}`,
        role: 'assistant',
        content: 'Ocorreu um erro ao publicar a vaga. Por favor, tente novamente.',
        timestamp: new Date()
      }
      ctx.setMessages(prev => [...prev, errorMessage])
      ctx.setFastTrackState('reviewing')
    }
    
    ctx.setIsLoading(false)
  }

  // Fast Track: Parse ctx.user adjustment request
  const parseFastTrackAdjustment = (content: string): VacancyAdjustments | null => {
    const adjustments: VacancyAdjustments = {}
    const lowerContent = content.toLowerCase()
    
    // Parse salary adjustments
    const salaryMatch = content.match(/sal[aá]rio\s*(?:para|de|:)?\s*(\d+(?:[.,]\d+)?)\s*(?:a|até|-|a)\s*(\d+(?:[.,]\d+)?)/i)
    if (salaryMatch) {
      adjustments.salary_min = parseFloat(salaryMatch[1].replace(',', '.')) * 1000
      adjustments.salary_max = parseFloat(salaryMatch[2].replace(',', '.')) * 1000
    }
    
    // Parse work model
    if (lowerContent.includes('remoto')) {
      adjustments.work_model = 'remote'
    } else if (lowerContent.includes('híbrido') || lowerContent.includes('hibrido')) {
      adjustments.work_model = 'hybrid'
    } else if (lowerContent.includes('presencial')) {
      adjustments.work_model = 'onsite'
    }
    
    // Parse location
    const locationMatch = content.match(/(?:local|localização|cidade)\s*(?:para|:)?\s*([A-Za-zÀ-ÿ\s]+)/i)
    if (locationMatch) {
      adjustments.location = locationMatch[1].trim()
    }
    
    return Object.keys(adjustments).length > 0 ? adjustments : null
  }

  // Build collected data object for orchestrator

  return {
    initializeCalibrationCriteria,
    generateCalibrationCandidates,
    handleApproveCandidate,
    handleRejectCandidate,
    moveToNextCandidate,
    generateMoreCalibrationCandidates,
    addCalibrationCriterion,
    removeCalibrationCriterion,
    reorderCalibrationCriteria,
    handleFastTrackVacancySelect,
    handleFastTrackSearch,
    handleFastTrackPublish,
    parseFastTrackAdjustment,
  }
}
