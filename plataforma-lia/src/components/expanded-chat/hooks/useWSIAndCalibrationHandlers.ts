"use client"

import React, { useCallback, useEffect } from "react"
import { liaApi, type WizardOrchestratorResponse, type VacancySearchCriteria, type VacancyAdjustments } from "@/services/lia-api"
import {
  type TechnicalSkill,
  type BehavioralCompetency,
  type SalaryInfo,
  type DetectedCriteria,
  type BasicInfoFields,
} from "../ExpandedChatContext"
import { type WizardStage, getFrontendStageFromBackend } from "../config/wizard-config"
import {
  type Message,
  type CalibrationCandidate,
  type WSIQuestionCandidate,
} from "../types"
import { type EnrichedJDData } from "../stages"
import { type WizardMode, type FastTrackState } from "../types"
import { type UseConversationMemoryReturn } from "./useConversationMemory"

export interface WSIAndCalibrationHandlersContext {
  // Basic info and criteria
  basicInfoFields: BasicInfoFields
  setBasicInfoFields: React.Dispatch<React.SetStateAction<BasicInfoFields>>
  detectedCriteria: DetectedCriteria
  setDetectedCriteria: React.Dispatch<React.SetStateAction<DetectedCriteria>>

  // Skills and competencies
  technicalSkills: TechnicalSkill[]
  setTechnicalSkills: React.Dispatch<React.SetStateAction<TechnicalSkill[]>>
  behavioralCompetencies: BehavioralCompetency[]
  setBehavioralCompetencies: React.Dispatch<React.SetStateAction<BehavioralCompetency[]>>

  // Salary
  salaryInfo: SalaryInfo
  setSalaryInfo: React.Dispatch<React.SetStateAction<SalaryInfo>>

  // Messages
  messages: Message[]
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>

  // Stage
  currentStage: WizardStage
  setCurrentStage: React.Dispatch<React.SetStateAction<WizardStage>>

  // WSI state
  wsiCandidates: WSIQuestionCandidate[]
  setWsiCandidates: React.Dispatch<React.SetStateAction<WSIQuestionCandidate[]>>
  wsiGenerationBatch: number
  setWsiGenerationBatch: React.Dispatch<React.SetStateAction<number>>
  isGeneratingWSI: boolean
  setIsGeneratingWSI: React.Dispatch<React.SetStateAction<boolean>>
  wsiHasGenerated: boolean
  setWsiHasGenerated: React.Dispatch<React.SetStateAction<boolean>>
  setWsiQuestions: React.Dispatch<React.SetStateAction<any[]>>
  customQuestionText: string
  customQuestionType: 'open' | 'yes-no' | 'numeric' | 'multiple-choice'
  customQuestionRequired: boolean
  setShowCustomQuestionForm: (val: boolean) => void
  setCustomQuestionText: (val: string) => void
  setCustomQuestionType: (val: 'open' | 'yes-no' | 'numeric' | 'multiple-choice') => void
  setCustomQuestionRequired: (val: boolean) => void

  // Calibration state
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
  publishedJobId: string | null
  setPublishedJobId: React.Dispatch<React.SetStateAction<string | null>>
  calibrationCriteria: Array<{ id: string; text: string; source: 'technical' | 'behavioral' }>
  setCalibrationCriteria: React.Dispatch<React.SetStateAction<Array<{ id: string; text: string; source: 'technical' | 'behavioral' }>>>
  postCalibrationComplete: boolean
  setPostCalibrationComplete: React.Dispatch<React.SetStateAction<boolean>>
  hasAttemptedCalibrationGeneration: boolean
  setHasAttemptedCalibrationGeneration: React.Dispatch<React.SetStateAction<boolean>>
  setSearchPhase: React.Dispatch<React.SetStateAction<'local-searching' | 'local-complete' | 'global-searching' | 'global-complete' | 'idle'>>
  setLocalCandidateCount: (count: number) => void
  setGlobalCandidateCount: (count: number) => void
  preferredCandidateCount: number
  awaitingCalibrationChoice: boolean
  setAwaitingCalibrationChoice: React.Dispatch<React.SetStateAction<boolean>>

  // Fast Track state
  fastTrackState: FastTrackState
  setFastTrackState: React.Dispatch<React.SetStateAction<FastTrackState>>
  fastTrackSelectedVacancy: any | null
  setFastTrackSelectedVacancy: (vacancy: any | null) => void
  fastTrackAdjustments: VacancyAdjustments
  setFastTrackAdjustments: React.Dispatch<React.SetStateAction<VacancyAdjustments>>
  fastTrackSearchResults: any[]
  setFastTrackSearchResults: React.Dispatch<React.SetStateAction<any[]>>
  isSearchingVacancies: boolean
  setIsSearchingVacancies: React.Dispatch<React.SetStateAction<boolean>>
  wizardFastTrackSourceJobId: string | null
  setWizardFastTrackSourceJobId: (id: string | null) => void
  setWizardMode: React.Dispatch<React.SetStateAction<WizardMode>>

  // Loading
  isLoading: boolean
  setIsLoading: React.Dispatch<React.SetStateAction<boolean>>

  // Job config
  setJobConfig: React.Dispatch<React.SetStateAction<any>>

  // Enrichment
  setEnrichedJDData: React.Dispatch<React.SetStateAction<EnrichedJDData | null>>
  setIsLoadingEnrichment: React.Dispatch<React.SetStateAction<boolean>>

  // Compensation
  setCompensationAnalysis: React.Dispatch<React.SetStateAction<any>>

  // Display state
  setDisplayedText: React.Dispatch<React.SetStateAction<string>>

  // User
  user: { name?: string; email?: string; company?: string; id?: string } | null

  // Conversation memory
  conversationMemory: UseConversationMemoryReturn

  // UI helpers
  highlightField: (field: string) => void
  typeText: (text: string, messageId: string) => void

  // Proactive confirmation tracking
  inputEvaluationStageCompletionShown: boolean
  awaitingStageAdvanceConfirmation: string | null
  setAwaitingStageAdvanceConfirmation: React.Dispatch<React.SetStateAction<string | null>>

  // Callback from parent
  onJobCreated?: () => void

  // From Extraction 1 — generateParecerData is needed by processOrchestratorResponse callers
  // (not directly by processOrchestratorResponse itself — it uses typeText + setMessages)
}

export function useWSIAndCalibrationHandlers(ctx: WSIAndCalibrationHandlersContext) {

  const generateWSIQuestions = async (count: number = 7, category: 'technical' | 'behavioral' = 'technical') => {
    ctx.setIsGeneratingWSI(true)
    const newBatch = ctx.wsiGenerationBatch + 1
    ctx.setWsiGenerationBatch(newBatch)
    
    try {
      // Call backend API to generate WSI questions using LLM
      const response = await liaApi.generateJobScreeningQuestions({
        job_title: ctx.basicInfoFields.cargo || 'Vaga',
        job_description: ctx.detectedCriteria.cargo ? `Vaga de ${ctx.detectedCriteria.cargo}` : undefined,
        technical_skills: ctx.technicalSkills.filter(s => s.required).map(s => s.name),
        behavioral_competencies: ctx.behavioralCompetencies.filter(c => c.enabled).map(c => c.name),
        seniority_level: ctx.detectedCriteria.senioridadeIdiomas?.toLowerCase() || 'pleno',
        work_model: ctx.basicInfoFields.modeloTrabalho?.toLowerCase(),
        location: ctx.basicInfoFields.localidade,
        count: count,
        category: category
      })
      
      // Convert API response to WSIQuestionCandidate format
      const existingTexts = new Set(ctx.wsiCandidates.map(q => q.question.toLowerCase()))
      
      const newQuestions: WSIQuestionCandidate[] = response.questions
        .filter(q => !existingTexts.has(q.question.toLowerCase()))
        .map((q) => ({
          id: q.id,
          question: q.question,
          type: q.type as 'open' | 'yes-no' | 'numeric' | 'multiple-choice',
          required: q.required,
          options: q.options,
          expectedAnswer: q.expected_answer,
          correctOptionIndex: q.correct_option_index,
          selected: false,
          batch: newBatch,
          isWSI: true,
          competency: q.competency,
          framework: q.framework,
          category: q.category
        }))
      
      ctx.setWsiCandidates(prev => [...prev, ...newQuestions])
      ctx.setWsiHasGenerated(true)
      
      // Add LIA feedback message
      const selectedCount = ctx.wsiCandidates.filter(q => q.selected).length
      const feedbackMessage: Message = {
        id: `wsi-feedback-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
        role: 'assistant',
        content: newBatch === 1 
          ? `Gerei ${newQuestions.length} perguntas de triagem baseadas na **metodologia WSI** (Work Sample Interview) e no perfil da vaga.\n\nAs perguntas foram criadas com base em frameworks científicos:\n- **CBI** (Competency-Based Interviewing)\n- **Dreyfus Model** (Avaliação de Expertise)\n- **Bloom's Taxonomy** (Níveis de Conhecimento)\n\nSelecione **5 perguntas** que melhor se adequam ao processo seletivo. As respostas esperadas já foram definidas pela LIA com base no perfil ideal.`
          : `Adicionei mais ${newQuestions.length} opções de perguntas WSI! Você tem ${selectedCount}/5 selecionadas.`,
        timestamp: new Date()
      }
      ctx.setMessages(prev => [...prev, feedbackMessage])
      
    } catch (error) {
      
      // Fallback to static questions if API fails
      const baseTs = Date.now()
      const fallbackQuestions: WSIQuestionCandidate[] = [
        { id: `wsi-fallback-${baseTs}-1-${Math.random().toString(36).slice(2, 8)}`, question: 'Qual sua pretensão salarial para regime CLT?', type: 'open', required: true, selected: false, batch: newBatch },
        { id: `wsi-fallback-${baseTs}-2-${Math.random().toString(36).slice(2, 8)}`, question: `Você tem disponibilidade para trabalho ${ctx.basicInfoFields.modeloTrabalho || 'híbrido'}${ctx.basicInfoFields.localidade ? ` em ${ctx.basicInfoFields.localidade}` : ''}?`, type: 'yes-no', required: true, expectedAnswer: true, selected: false, batch: newBatch },
        { id: `wsi-fallback-${baseTs}-3-${Math.random().toString(36).slice(2, 8)}`, question: 'Quantos anos de experiência você tem com a principal tecnologia da vaga?', type: 'numeric', required: true, expectedAnswer: 3, selected: false, batch: newBatch },
        { id: `wsi-fallback-${baseTs}-4-${Math.random().toString(36).slice(2, 8)}`, question: 'Você tem experiência com metodologias ágeis (Scrum, Kanban)?', type: 'yes-no', required: true, expectedAnswer: true, selected: false, batch: newBatch },
        { id: `wsi-fallback-${baseTs}-5-${Math.random().toString(36).slice(2, 8)}`, question: 'Qual seu nível de inglês?', type: 'multiple-choice', options: ['Básico', 'Intermediário', 'Avançado', 'Fluente'], required: true, correctOptionIndex: 2, selected: false, batch: newBatch },
      ]
      
      const existingTexts = new Set(ctx.wsiCandidates.map(q => q.question.toLowerCase()))
      const newQuestions = fallbackQuestions.filter(q => !existingTexts.has(q.question.toLowerCase())).slice(0, count)
      
      ctx.setWsiCandidates(prev => [...prev, ...newQuestions])
      ctx.setWsiHasGenerated(true)
      
      const feedbackMessage: Message = {
        id: `wsi-feedback-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
        role: 'assistant',
        content: `Gerei ${newQuestions.length} perguntas de triagem padrão. Selecione **5 perguntas** para a triagem.`,
        timestamp: new Date()
      }
      ctx.setMessages(prev => [...prev, feedbackMessage])
    } finally {
      ctx.setIsGeneratingWSI(false)
    }
  }

  const toggleWSIQuestionSelection = (questionId: string) => {
    ctx.setWsiCandidates(prev => {
      const currentlySelected = prev.filter(q => q.selected).length
      const question = prev.find(q => q.id === questionId)
      
      if (!question) return prev
      
      // If already at max (5) and trying to select more, don't allow
      if (!question.selected && currentlySelected >= 5) {
        return prev
      }
      
      const updated = prev.map(q => 
        q.id === questionId ? { ...q, selected: !q.selected } : q
      )
      
      // Sync selected questions to wsiQuestions
      const selected = updated.filter(q => q.selected)
      ctx.setWsiQuestions(selected.map(({ selected, batch, ...rest }) => rest))
      
      // If reached 5 questions, add confirmation message
      const newCount = question.selected ? currentlySelected - 1 : currentlySelected + 1
      if (newCount === 5) {
        const confirmMessage: Message = {
          id: `wsi-confirm-${Date.now()}`,
          role: 'assistant',
          content: `Perfeito! Você selecionou **5 perguntas** de triagem.\n\nRevise as respostas esperadas no painel e clique em "Confirmar Triagem" quando estiver pronto para a revisão final.`,
          timestamp: new Date()
        }
        ctx.setMessages(msgs => [...msgs, confirmMessage])
      }
      
      return updated
    })
  }

  const updateWSIQuestionExpectedAnswer = (questionId: string, answer: string | number | boolean) => {
    ctx.setWsiCandidates(prev => {
      const updated = prev.map(q => 
        q.id === questionId ? { ...q, expectedAnswer: answer } : q
      )
      // Sync to wsiQuestions
      const selected = updated.filter(q => q.selected)
      ctx.setWsiQuestions(selected.map(({ selected, batch, ...rest }) => rest))
      return updated
    })
  }

  const updateWSIQuestionCorrectOption = (questionId: string, optionIndex: number) => {
    ctx.setWsiCandidates(prev => {
      const updated = prev.map(q => 
        q.id === questionId ? { ...q, correctOptionIndex: optionIndex } : q
      )
      // Sync to wsiQuestions
      const selected = updated.filter(q => q.selected)
      ctx.setWsiQuestions(selected.map(({ selected, batch, ...rest }) => rest))
      return updated
    })
  }

  const deleteWSIQuestion = (questionId: string) => {
    ctx.setWsiCandidates(prev => {
      const updated = prev.filter(q => q.id !== questionId)
      const selected = updated.filter(q => q.selected)
      ctx.setWsiQuestions(selected.map(({ selected, batch, ...rest }) => rest))
      return updated
    })
  }

  const addCustomQuestion = () => {
    if (!ctx.customQuestionText.trim()) return
    
    const newQuestion: WSIQuestionCandidate = {
      id: `custom-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      question: ctx.customQuestionText.trim(),
      type: ctx.customQuestionType,
      required: ctx.customQuestionRequired,
      selected: false,
      batch: ctx.wsiGenerationBatch,
      isWSI: false,
      category: 'technical'
    }
    
    ctx.setWsiCandidates(prev => [...prev, newQuestion])
    ctx.setShowCustomQuestionForm(false)
    ctx.setCustomQuestionText('')
    ctx.setCustomQuestionType('open')
    ctx.setCustomQuestionRequired(false)
  }

  // Auto-generate WSI questions when entering the stage
  useEffect(() => {
    if (ctx.currentStage === 'wsi-questions' && !ctx.wsiHasGenerated && !ctx.isGeneratingWSI) {
      // Generate technical questions first
      generateWSIQuestions(7, 'technical')
      // Also generate behavioral/fit questions (3-5 based on selected competencies)
      const enabledBehavioralCount = ctx.behavioralCompetencies.filter(c => c.enabled).length
      const behavioralQuestionCount = Math.max(3, Math.min(5, enabledBehavioralCount))
      setTimeout(() => {
        generateWSIQuestions(behavioralQuestionCount, 'behavioral')
      }, 1500) // Small delay to avoid race conditions
    }
  }, [ctx.currentStage, ctx.wsiHasGenerated, ctx.isGeneratingWSI])

  // Initialize calibration criteria from technical skills and behavioral competencies
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
  }, [ctx.technicalSkills, ctx.behavioralCompetencies])

  // Generate calibration candidates from real API
  const generateCalibrationCandidates = async () => {
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
  }

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
  }, [ctx.currentStage, ctx.calibrationCandidates.length, ctx.isLoadingCalibration, ctx.hasAttemptedCalibrationGeneration, initializeCalibrationCriteria])

  // Fast Track: Handle vacancy selection
  const handleFastTrackVacancySelect = async (vacancyId: string) => {
    ctx.setIsLoading(true)
    
    try {
      const vacancyDetails = await liaApi.getVacancyFullDetails(vacancyId)
      
      if (vacancyDetails) {
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
  const buildCollectedData = useCallback(() => {
    return {
      title: ctx.basicInfoFields.cargo || ctx.detectedCriteria.cargo || null,
      department: ctx.basicInfoFields.area || ctx.detectedCriteria.departamento || null,
      seniority_level: ctx.detectedCriteria.senioridadeIdiomas || null,
      work_model: ctx.basicInfoFields.modeloTrabalho || ctx.detectedCriteria.modeloTrabalho || null,
      location: ctx.basicInfoFields.localidade || ctx.detectedCriteria.localizacao || null,
      manager: ctx.basicInfoFields.gestor || ctx.detectedCriteria.gestorArea || null,
      salary_min: ctx.salaryInfo.minSalary ? parseInt(ctx.salaryInfo.minSalary) : null,
      salary_max: ctx.salaryInfo.maxSalary ? parseInt(ctx.salaryInfo.maxSalary) : null,
      technical_skills: ctx.technicalSkills.filter(s => s.required).map(s => s.name),
      behavioral_competencies: ctx.behavioralCompetencies.filter(c => c.enabled).map(c => c.name),
      screening_questions: ctx.wsiCandidates.filter(q => q.selected).map(q => ({
        question: q.question,
        category: q.category,
        expected_answer: q.expectedAnswer,
        weight: 5,
        type: q.type
      }))
    }
  }, [ctx.basicInfoFields, ctx.detectedCriteria, ctx.salaryInfo, ctx.technicalSkills, ctx.behavioralCompetencies, ctx.wsiCandidates])

  // Process orchestrator response and apply actions from smart-orchestrate endpoint
  const processOrchestratorResponse = useCallback(async (
    orchestratorResult: WizardOrchestratorResponse,
    processingMessageId: string
  ) => {
    
    // Use new response format from smart-orchestrate endpoint
    const liaMessage = orchestratorResult.lia_message || orchestratorResult.response || ''
    const detectedCriteriaFromBackend = orchestratorResult.detected_criteria || {}
    const nextStage = orchestratorResult.next_stage
    const autoTransition = orchestratorResult.auto_transition
    const toolResults = orchestratorResult.tool_results || []
    
    // Update processing message
    ctx.setMessages(msgs => msgs.map(m => 
      m.id === processingMessageId 
        ? { ...m, content: '✅ Resposta da LIA', processingState: 'completed' as const }
        : m
    ))
    
    // Apply detected_criteria to form fields
    if (detectedCriteriaFromBackend && Object.keys(detectedCriteriaFromBackend).length > 0) {
      
      // Job title / cargo
      if (detectedCriteriaFromBackend.job_title || detectedCriteriaFromBackend.title || detectedCriteriaFromBackend.cargo) {
        const title = detectedCriteriaFromBackend.job_title || detectedCriteriaFromBackend.title || detectedCriteriaFromBackend.cargo
        ctx.setBasicInfoFields(prev => ({ ...prev, cargo: title }))
        ctx.setDetectedCriteria(prev => ({ ...prev, cargo: title }))
        ctx.highlightField('cargo')
      }
      
      // Department / area
      if (detectedCriteriaFromBackend.department || detectedCriteriaFromBackend.area) {
        const dept = detectedCriteriaFromBackend.department || detectedCriteriaFromBackend.area
        ctx.setBasicInfoFields(prev => ({ ...prev, area: dept }))
        ctx.setDetectedCriteria(prev => ({ ...prev, departamento: dept }))
        ctx.highlightField('departamento')
      }
      
      // Seniority
      if (detectedCriteriaFromBackend.seniority || detectedCriteriaFromBackend.seniority_level) {
        const seniority = detectedCriteriaFromBackend.seniority || detectedCriteriaFromBackend.seniority_level
        ctx.setDetectedCriteria(prev => ({ ...prev, senioridadeIdiomas: seniority }))
        ctx.highlightField('senioridade')
      }
      
      // Work model
      if (detectedCriteriaFromBackend.work_model || detectedCriteriaFromBackend.modelo_trabalho) {
        const workModel = detectedCriteriaFromBackend.work_model || detectedCriteriaFromBackend.modelo_trabalho
        ctx.setBasicInfoFields(prev => ({ ...prev, modeloTrabalho: workModel }))
        ctx.setDetectedCriteria(prev => ({ ...prev, modeloTrabalho: workModel }))
        ctx.highlightField('modeloTrabalho')
      }
      
      // Location
      if (detectedCriteriaFromBackend.location || detectedCriteriaFromBackend.localidade) {
        const location = detectedCriteriaFromBackend.location || detectedCriteriaFromBackend.localidade
        ctx.setBasicInfoFields(prev => ({ ...prev, localidade: location }))
        ctx.setDetectedCriteria(prev => ({ ...prev, localizacao: location }))
        ctx.highlightField('localizacao')
      }
      
      // Manager / Gestor
      if (detectedCriteriaFromBackend.manager || detectedCriteriaFromBackend.gestor) {
        const manager = detectedCriteriaFromBackend.manager || detectedCriteriaFromBackend.gestor
        ctx.setBasicInfoFields(prev => ({ ...prev, gestor: manager }))
        ctx.setDetectedCriteria(prev => ({ ...prev, gestorArea: manager }))
        ctx.highlightField('gestor')
      }
      
      // Salary
      if (detectedCriteriaFromBackend.salary_min || detectedCriteriaFromBackend.min_salary) {
        const minSalary = detectedCriteriaFromBackend.salary_min || detectedCriteriaFromBackend.min_salary
        ctx.setSalaryInfo(prev => ({ ...prev, minSalary: minSalary.toString() }))
        ctx.highlightField('minSalary')
      }
      if (detectedCriteriaFromBackend.salary_max || detectedCriteriaFromBackend.max_salary) {
        const maxSalary = detectedCriteriaFromBackend.salary_max || detectedCriteriaFromBackend.max_salary
        ctx.setSalaryInfo(prev => ({ ...prev, maxSalary: maxSalary.toString() }))
        ctx.highlightField('maxSalary')
      }

      if (ctx.currentStage === 'salary') {
        const salaryDetectedFields: Array<{ label: string; value: string; confidence?: "high" | "medium" | "low" }> = []
        const detectedMin = detectedCriteriaFromBackend.salary_min || detectedCriteriaFromBackend.min_salary
        const detectedMax = detectedCriteriaFromBackend.salary_max || detectedCriteriaFromBackend.max_salary
        if (detectedMin) salaryDetectedFields.push({ label: "Salário Mínimo", value: `R$ ${detectedMin}`, confidence: "high" })
        if (detectedMax) salaryDetectedFields.push({ label: "Salário Máximo", value: `R$ ${detectedMax}`, confidence: "high" })
        if (detectedCriteriaFromBackend.bonus_min) salaryDetectedFields.push({ label: "Bônus Mínimo", value: `${detectedCriteriaFromBackend.bonus_min}%`, confidence: "medium" })
        if (detectedCriteriaFromBackend.bonus_max) salaryDetectedFields.push({ label: "Bônus Máximo", value: `${detectedCriteriaFromBackend.bonus_max}%`, confidence: "medium" })

        if (salaryDetectedFields.length > 0) {
          const salaryDetectedMsg: Message = {
            id: `salary-detected-${Date.now()}`,
            role: 'assistant',
            content: '',
            timestamp: new Date(),
            messageType: 'detected-fields',
            detectedFields: salaryDetectedFields
          }
          ctx.setMessages(prev => [...prev, salaryDetectedMsg])
        }
      }
      
      // Technical skills
      if (detectedCriteriaFromBackend.technical_skills && Array.isArray(detectedCriteriaFromBackend.technical_skills)) {
        const newSkills = detectedCriteriaFromBackend.technical_skills as string[]
        newSkills.forEach((skill: string, index: number) => {
          if (!ctx.technicalSkills.find(s => s.name.toLowerCase() === skill.toLowerCase())) {
            ctx.setTechnicalSkills(prev => [
              ...prev,
              {
                id: `smart-skill-${Date.now()}-${index}`,
                name: skill,
                level: 'Intermediário' as const,
                required: true,
                category: 'tool' as const,
                weight: 3
              }
            ])
          }
        })
        if (newSkills.length > 0) {
          ctx.highlightField('skills')
        }
      }
      
      // Behavioral competencies
      if (detectedCriteriaFromBackend.behavioral_competencies && Array.isArray(detectedCriteriaFromBackend.behavioral_competencies)) {
        const newComps = detectedCriteriaFromBackend.behavioral_competencies as string[]
        newComps.forEach((comp: string) => {
          const existing = ctx.behavioralCompetencies.find(c => c.name.toLowerCase() === comp.toLowerCase())
          if (existing && !existing.enabled) {
            ctx.setBehavioralCompetencies(prev => prev.map(c => 
              c.name.toLowerCase() === comp.toLowerCase() ? { ...c, enabled: true } : c
            ))
          }
        })
        if (newComps.length > 0) {
          ctx.highlightField('competencias')
        }
      }

      if (ctx.currentStage === 'competencies') {
        const compDetectedFields: Array<{ label: string; value: string; confidence?: "high" | "medium" | "low" }> = []
        const detectedTechSkills = detectedCriteriaFromBackend.technical_skills || detectedCriteriaFromBackend.required_skills || detectedCriteriaFromBackend.competenciasTecnicas || []
        const detectedBehavSkills = detectedCriteriaFromBackend.behavioral_competencies || detectedCriteriaFromBackend.competenciasComportamentais || []

        if (Array.isArray(detectedTechSkills) && detectedTechSkills.length > 0) {
          compDetectedFields.push({ label: "Skills Técnicas", value: detectedTechSkills.slice(0, 5).join(", "), confidence: "high" })
        }
        if (Array.isArray(detectedBehavSkills) && detectedBehavSkills.length > 0) {
          compDetectedFields.push({ label: "Competências Comportamentais", value: detectedBehavSkills.slice(0, 3).join(", "), confidence: "medium" })
        }

        if (compDetectedFields.length > 0) {
          const compDetectedMsg: Message = {
            id: `comp-detected-${Date.now()}`,
            role: 'assistant',
            content: '',
            timestamp: new Date(),
            messageType: 'detected-fields',
            detectedFields: compDetectedFields
          }
          ctx.setMessages(prev => [...prev, compDetectedMsg])
        }
      }
      
      // Affirmative action
      if (detectedCriteriaFromBackend.is_affirmative !== undefined) {
        ctx.setDetectedCriteria(prev => ({ ...prev, isAffirmative: detectedCriteriaFromBackend.is_affirmative }))
        ctx.setJobConfig(prev => ({ ...prev, isAffirmative: detectedCriteriaFromBackend.is_affirmative }))
      }
      
      // Responsibilities / Responsabilidades
      if (detectedCriteriaFromBackend.responsibilities && Array.isArray(detectedCriteriaFromBackend.responsibilities)) {
        const newResponsibilities = detectedCriteriaFromBackend.responsibilities as string[]
        if (newResponsibilities.length > 0) {
          ctx.setDetectedCriteria(prev => ({
            ...prev,
            responsabilidades: [...new Set([...(prev.responsabilidades || []), ...newResponsibilities])]
          }))
          ctx.highlightField('responsabilidades')
        }
      }
      
      // Helper function for case-insensitive deduplication while preserving original casing
      const deduplicateCaseInsensitive = (existing: string[], newItems: string[]): string[] => {
        const seen = new Map<string, string>()
        // Add existing items first
        existing.forEach(item => {
          const key = item.toLowerCase()
          if (!seen.has(key)) seen.set(key, item)
        })
        // Add new items only if not already present (case-insensitive)
        newItems.forEach(item => {
          const key = item.toLowerCase()
          if (!seen.has(key)) seen.set(key, item)
        })
        return Array.from(seen.values())
      }
      
      // Required skills (also maps to technical skills)
      if (detectedCriteriaFromBackend.required_skills && Array.isArray(detectedCriteriaFromBackend.required_skills)) {
        const newSkills = detectedCriteriaFromBackend.required_skills as string[]
        newSkills.forEach((skill: string, index: number) => {
          if (!ctx.technicalSkills.find(s => s.name.toLowerCase() === skill.toLowerCase())) {
            ctx.setTechnicalSkills(prev => [
              ...prev,
              {
                id: `smart-skill-${Date.now()}-${index}`,
                name: skill,
                level: 'Intermediário' as const,
                required: true,
                category: 'tool' as const,
                weight: 3
              }
            ])
          }
        })
        // Also update detected criteria for panel display
        if (newSkills.length > 0) {
          ctx.setDetectedCriteria(prev => ({
            ...prev,
            competenciasTecnicas: deduplicateCaseInsensitive(prev.competenciasTecnicas || [], newSkills)
          }))
          ctx.highlightField('skills')
        }
      }
      
      // Soft skills (also maps to behavioral competencies display)
      if (detectedCriteriaFromBackend.soft_skills && Array.isArray(detectedCriteriaFromBackend.soft_skills)) {
        const newComps = detectedCriteriaFromBackend.soft_skills as string[]
        if (newComps.length > 0) {
          ctx.setDetectedCriteria(prev => ({
            ...prev,
            competenciasComportamentais: deduplicateCaseInsensitive(prev.competenciasComportamentais || [], newComps)
          }))
          ctx.highlightField('competencias')
        }
      }
    }
    
    // Process tool_results if present (e.g., salary benchmark, skills suggestions)
    if (toolResults.length > 0) {
      toolResults.forEach((toolResult: any) => {
        if (toolResult.tool === 'salary_benchmark' && toolResult.result) {
          ctx.setCompensationAnalysis(toolResult.result)
        }
        if (toolResult.tool === 'skills_suggestion' && toolResult.result?.skills) {
          const suggestedSkills = toolResult.result.skills
          suggestedSkills.forEach((skill: any, index: number) => {
            if (!ctx.technicalSkills.find(s => s.name.toLowerCase() === skill.name?.toLowerCase())) {
              ctx.setTechnicalSkills(prev => [
                ...prev,
                {
                  id: `tool-skill-${Date.now()}-${index}`,
                  name: skill.name,
                  level: skill.level || 'Intermediário',
                  required: skill.required ?? true,
                  category: skill.category || 'tool',
                  weight: skill.weight || 3
                }
              ])
            }
          })
        }
        // Process JD enrichment data
        if (toolResult.tool === 'generate_enriched_jd' && toolResult.result) {
          const enrichmentResult = toolResult.result
          // Map backend response to EnrichedJDData format
          const enrichedData: EnrichedJDData = {
            sections: enrichmentResult.sections || [],
            compensation: enrichmentResult.compensation,
            wsiQualityScore: enrichmentResult.wsi_quality_score ?? enrichmentResult.wsiQualityScore ?? 0,
            overallCompleteness: enrichmentResult.overall_completeness ?? enrichmentResult.overallCompleteness ?? 0,
            totalSuggestions: enrichmentResult.total_suggestions ?? enrichmentResult.totalSuggestions ?? 0
          }
          ctx.setEnrichedJDData(enrichedData)
          ctx.setIsLoadingEnrichment(false)
        }
      })
    }
    
    // Handle action results from WizardActionExecutor
    if (orchestratorResult.action_executed && orchestratorResult.action_type) {
      
      // Apply draft_updates to form fields if present
      if (orchestratorResult.draft_updates && Object.keys(orchestratorResult.draft_updates).length > 0) {
        const updates = orchestratorResult.draft_updates as Record<string, any>
        if (updates.cargo || updates.job_title || updates.title) {
          const title = updates.cargo || updates.job_title || updates.title
          ctx.setBasicInfoFields(prev => ({ ...prev, cargo: title }))
          ctx.highlightField('cargo')
        }
        if (updates.area || updates.department) {
          const dept = updates.area || updates.department
          ctx.setBasicInfoFields(prev => ({ ...prev, area: dept }))
          ctx.highlightField('departamento')
        }
        if (updates.localidade || updates.location) {
          const location = updates.localidade || updates.location
          ctx.setBasicInfoFields(prev => ({ ...prev, localidade: location }))
          ctx.highlightField('localizacao')
        }
        if (updates.modeloTrabalho || updates.work_model) {
          const workModel = updates.modeloTrabalho || updates.work_model
          ctx.setBasicInfoFields(prev => ({ ...prev, modeloTrabalho: workModel }))
          ctx.highlightField('modeloTrabalho')
        }
        if (updates.gestor || updates.manager) {
          const manager = updates.gestor || updates.manager
          ctx.setBasicInfoFields(prev => ({ ...prev, gestor: manager }))
          ctx.highlightField('gestor')
        }
      }
      
      // Add action result message to chat
      const actionResultMsg: Message = {
        id: `action-result-${Date.now()}`,
        role: 'assistant',
        content: liaMessage,
        timestamp: new Date(),
        messageType: 'action-result',
        actionType: orchestratorResult.action_type,
        actionResult: (orchestratorResult.action_result || {}) as Record<string, unknown>,
        isTyping: true
      }
      
      if (ctx.conversationMemory.conversationId) {
        ctx.conversationMemory.addMessage('assistant', liaMessage).catch(() => {})
      }
      
      setTimeout(() => {
        ctx.setMessages(prev => [...prev, actionResultMsg])
        ctx.typeText(liaMessage, actionResultMsg.id)
      }, 200)
      
      return
    }
    
    // Handle automatic stage transition
    if (autoTransition && nextStage) {
      const frontendStage = getFrontendStageFromBackend(nextStage)
      if (frontendStage && frontendStage !== ctx.currentStage) {
        setTimeout(() => {
          ctx.setCurrentStage(frontendStage as WizardStage)
        }, 1500)
      }
    }
    
    // Handle awaiting_confirmation from backend - show proactive message asking to advance
    const awaitingConfirmation = orchestratorResult.awaiting_confirmation
    const shouldShowProactiveConfirmation = awaitingConfirmation && 
      ctx.currentStage === 'input-evaluation' && 
      !ctx.awaitingStageAdvanceConfirmation && // Not already awaiting confirmation
      Object.keys(detectedCriteriaFromBackend).length > 0 // Has detected criteria
    
    if (shouldShowProactiveConfirmation) {
      
      // Build summary of detected fields (support both snake_case and camelCase)
      const detectedFields: string[] = []
      const title = detectedCriteriaFromBackend.job_title || detectedCriteriaFromBackend.title || detectedCriteriaFromBackend.cargo
      const seniority = detectedCriteriaFromBackend.seniority || detectedCriteriaFromBackend.senioridade
      const department = detectedCriteriaFromBackend.department || detectedCriteriaFromBackend.departamento || detectedCriteriaFromBackend.area
      const techSkills = detectedCriteriaFromBackend.technical_skills || detectedCriteriaFromBackend.competenciasTecnicas || detectedCriteriaFromBackend.required_skills || []
      const salaryMin = detectedCriteriaFromBackend.salary_min || detectedCriteriaFromBackend.salarioMin
      const salaryMax = detectedCriteriaFromBackend.salary_max || detectedCriteriaFromBackend.salarioMax
      
      if (title) detectedFields.push(`Cargo: **${title}**`)
      if (seniority) detectedFields.push(`Senioridade: **${seniority}**`)
      if (department) detectedFields.push(`Departamento: **${department}**`)
      if (techSkills?.length > 0) detectedFields.push(`Skills Técnicas: **${techSkills.slice(0, 3).join(', ')}**`)
      if (salaryMin && salaryMax) {
        const minFormatted = typeof salaryMin === 'number' ? salaryMin.toLocaleString('pt-BR') : salaryMin
        const maxFormatted = typeof salaryMax === 'number' ? salaryMax.toLocaleString('pt-BR') : salaryMax
        detectedFields.push(`Faixa Salarial: **R$ ${minFormatted} - R$ ${maxFormatted}**`)
      }
      
      const summaryText = detectedFields.length > 0 
        ? `\n\n📋 **Critérios detectados:**\n${detectedFields.map(f => `• ${f}`).join('\n')}`
        : ''
      
      // Append proactive question to LIA's response
      const enhancedMessage = `${liaMessage}${summaryText}\n\n✨ Quer que eu avance para a etapa de **Enriquecimento da Vaga**, onde vou analisar dados de mercado e sugerir melhorias para a descrição?`
      
      // Build structured detected fields for DetectedFieldsCard
      const detectedFieldsStructured: Array<{ label: string; value: string; confidence?: "high" | "medium" | "low" }> = []
      if (title) detectedFieldsStructured.push({ label: "Cargo", value: String(title), confidence: "high" })
      if (seniority) detectedFieldsStructured.push({ label: "Senioridade", value: String(seniority), confidence: "high" })
      if (department) detectedFieldsStructured.push({ label: "Departamento", value: String(department), confidence: "medium" })
      if (techSkills?.length > 0) detectedFieldsStructured.push({ label: "Skills Técnicas", value: techSkills.slice(0, 5).join(", "), confidence: "high" })
      if (salaryMin && salaryMax) {
        const minF = typeof salaryMin === 'number' ? salaryMin.toLocaleString('pt-BR') : salaryMin
        const maxF = typeof salaryMax === 'number' ? salaryMax.toLocaleString('pt-BR') : salaryMax
        detectedFieldsStructured.push({ label: "Faixa Salarial", value: `R$ ${minF} - R$ ${maxF}`, confidence: "medium" })
      }

      // Set awaiting confirmation state
      ctx.setAwaitingStageAdvanceConfirmation('jd-enrichment')
      
      // Show enhanced message with proactive question
      const proactiveMsg: Message = {
        id: `lia-orchestrator-${Date.now()}`,
        role: 'assistant',
        content: enhancedMessage,
        timestamp: new Date(),
        isTyping: true,
        awaitingStageConfirmation: 'jd-enrichment',
        detectedFieldsData: detectedFieldsStructured
      }
      
      if (ctx.conversationMemory.conversationId) {
        ctx.conversationMemory.addMessage('assistant', enhancedMessage).catch(() => {})
      }
      
      setTimeout(() => {
        ctx.setMessages(prev => [...prev, proactiveMsg])
        ctx.typeText(enhancedMessage, proactiveMsg.id)
      }, 200)
      
      return // Show enhanced message instead of normal response
    }
    
    // Show orchestrator response
    const assistantMessage: Message = {
      id: `lia-orchestrator-${Date.now()}`,
      role: 'assistant',
      content: liaMessage,
      timestamp: new Date(),
      isTyping: true
    }
    
    // Save assistant message to conversation memory
    if (ctx.conversationMemory.conversationId) {
      ctx.conversationMemory.addMessage('assistant', liaMessage).catch(() => {})
    }
    
    setTimeout(() => {
      ctx.setMessages(prev => [...prev, assistantMessage])
      ctx.typeText(liaMessage, assistantMessage.id)
    }, 200)
  }, [ctx.typeText, ctx.conversationMemory.conversationId, ctx.highlightField, ctx.currentStage, ctx.technicalSkills, ctx.behavioralCompetencies, ctx.setJobConfig, ctx.inputEvaluationStageCompletionShown])

  // Fast Track: Detect ctx.user intent from message
  const detectFastTrackIntent = (content: string): 'fast_track' | 'from_scratch' | 'confirm' | 'adjust' | 'select' | 'criteria' | null => {
    const lowerContent = content.toLowerCase()
    
    // Detect confirmation
    if (lowerContent.includes('confirmar') || lowerContent.includes('publicar') || lowerContent === 'sim') {
      return 'confirm'
    }
    
    // Detect fast track intent
    if (lowerContent.includes('aproveitar') || lowerContent.includes('anterior') || 
        lowerContent.includes('reutilizar') || lowerContent.includes('copiar') ||
        lowerContent.includes('usar vaga') || lowerContent.includes('vaga passada')) {
      return 'fast_track'
    }
    
    // Detect create from scratch
    if (lowerContent.includes('do zero') || lowerContent.includes('criar nova') || 
        lowerContent.includes('nova vaga') || lowerContent.includes('começar')) {
      return 'from_scratch'
    }
    
    // Detect selection by number
    if (/^[1-9]$/.test(content.trim()) || /^(um|dois|três|quatro|cinco|seis|sete|oito|nove|dez)$/i.test(content.trim())) {
      return 'select'
    }
    
    // Detect adjustment request
    if (lowerContent.includes('mudar') || lowerContent.includes('alterar') || 
        lowerContent.includes('ajustar') || lowerContent.includes('salário para') ||
        lowerContent.includes('modelo') || lowerContent.includes('local para')) {
      return 'adjust'
    }
    
    // Check if it contains search criteria (title, department, manager)
    if (ctx.fastTrackState === 'collecting_criteria' || ctx.fastTrackState === 'initial') {
      return 'criteria'
    }
    
    return null
  }

  return {
    generateWSIQuestions,
    toggleWSIQuestionSelection,
    updateWSIQuestionExpectedAnswer,
    updateWSIQuestionCorrectOption,
    deleteWSIQuestion,
    addCustomQuestion,
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
    buildCollectedData,
    processOrchestratorResponse,
    detectFastTrackIntent,
  }
}
