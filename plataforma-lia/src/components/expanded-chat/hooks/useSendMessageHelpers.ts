import type { SendMessageHandlersContext } from './useSendMessageHandlers'
import type { Message } from '../types'
import type { VacancyFullDetails } from '@/components/job-creation/vacancy-full-summary'
import type { VacancySearchCriteria } from '@/services/lia-api'
import type { FastTrackSuggestion, FastTrackJobData } from '@/hooks/useFastTrack'
import type { WSIQuestion } from '../ExpandedChatContext'
import type { ParsedNavigationCommand, ParsedEditCommand } from '../utils'
import {
  WIZARD_STAGES,
  getStageTransitionMessage,
  FROM_SCRATCH_ORIENTATION_MESSAGE,
} from '../index'
import type { WizardStage } from '../config'
import {
  getConversationalResponse,
  orchestrateWizardMessage,
  interpretMessage,
} from '@/services/lia-api'
import { parseSalaryValue, applySalaryUpdate, addSkillIfNotExists, removeSkillByName, parseCommand, getStageLabel } from '../utils'

export async function handleStageAdvanceConfirmation(
  content: string,
  ctx: SendMessageHandlersContext
): Promise<boolean> {
  if (!ctx.awaitingStageAdvanceConfirmation) return false
  const lowerMessage = content.toLowerCase().trim()
  const originalMessage = content.trim()

  const adjustmentPatterns = [
    'ajust', 'alter', 'mud', 'troc', 'edit', 'corrig', 'revis',
    'quero', 'preciso', 'falta', 'adiciona', 'remov', 'exclui',
    'não', 'nao', 'errad', 'outr', 'diferent'
  ]
  const isAdjustmentRequest = adjustmentPatterns.some(p => lowerMessage.includes(p))

  const shortConfirmPatterns = [
    /^sim$/i, /^pode$/i, /^vamos$/i, /^ok$/i, /^beleza$/i, /^bora$/i,
    /^perfeito$/i, /^show$/i, /^massa$/i, /^confirmo$/i, /^confirma$/i,
    /^tá bom$/i, /^ta bom$/i, /^está bom$/i, /^ta certo$/i, /^tá certo$/i,
    /^pode ser$/i, /^pode sim$/i, /^sim,? pode$/i, /^vamos lá$/i,
    /^vamos sim$/i, /^avança$/i, /^avançar$/i, /^próxima$/i, /^proxima$/i,
    /^seguir$/i, /^segue$/i, /^prosseguir$/i, /^continuar$/i,
    /^sim,?\s*(pode|vamos|avança|ok|beleza)$/i,
    /^(pode|vamos|ok),?\s*sim$/i
  ]

  const isShortMessage = originalMessage.length <= 30
  const isStandaloneConfirmation = shortConfirmPatterns.some(p => p.test(lowerMessage))
  const isClearConfirmation = (isShortMessage && isStandaloneConfirmation && !isAdjustmentRequest)

  if (isClearConfirmation) {

    if (ctx.awaitingStageAdvanceConfirmation === 'calibration-complete') {
      ctx.setCalibrationComplete(true)
      const totalEvaluated = ctx.approvedCandidates.length + ctx.rejectedCandidates.length
      const completeMsg: Message = {
        id: `calibration-finished-${Date.now()}`,
        role: 'assistant',
        content: `🎯 **Calibração finalizada!**\n\nO modelo de busca foi ajustado com base nas suas ${totalEvaluated} avaliações. Agora as próximas buscas vão priorizar candidatos similares aos que você aprovou.`,
        timestamp: new Date(),
      }
      ctx.setMessages(prev => [...prev, completeMsg])
      ctx.setAwaitingStageAdvanceConfirmation(null)
      return true
    }

    const nextStage = ctx.awaitingStageAdvanceConfirmation

    if (nextStage === 'jd-enrichment') {
      ctx.setAwaitingStageAdvanceConfirmation(null)
      ctx.setIsLoadingEnrichment(true)
      const loadingMsg: Message = {
        id: `jd-enrichment-loading-${Date.now()}`,
        role: 'assistant',
        content: '🔍 **Analisando dados de mercado...**\n\nEstou consultando benchmarks salariais, catálogo de competências e histórico da empresa para preparar sugestões personalizadas.',
        timestamp: new Date(),
        isProcessing: true,
        processingState: 'analyzing'
      }
      ctx.setMessages(prev => [...prev, loadingMsg])
      ctx.setCurrentStage('jd-enrichment' as WizardStage)
      const collectedData = ctx.buildCollectedData()
      orchestrateWizardMessage({
        message: content,
        current_stage: 'input-evaluation',
        collected_data: collectedData,
        conversation_history: ctx.messages.slice(-10).map(m => ({ role: m.role, content: m.content })),
        conversation_id: ctx.conversationMemory.conversationId || undefined,
        company_id: ctx.user?.company || undefined,
        user_id: ctx.user?.email || undefined
      }).then(async result => {
        ctx.setMessages(prev => prev.filter(m => m.id !== loadingMsg.id))
        await ctx.processOrchestratorResponse(result, loadingMsg.id)
        ctx.setIsLoadingEnrichment(false)
        setTimeout(() => {
          const parecerData = ctx.generateParecerData()
          const parecerMsg: Message = {
            id: `parecer-lia-${Date.now()}`,
            role: 'assistant',
            content: `Preparei uma análise completa da sua vaga. Revise o parecer abaixo e ajuste o que desejar antes de avançarmos para **Remuneração**.`,
            timestamp: new Date(),
            messageType: 'parecer-lia',
            parecerData
          }
          ctx.setMessages(prev => [...prev, parecerMsg])
          ctx.setAwaitingStageAdvanceConfirmation('salary')
        }, 1000)
      }).catch(() => {
        ctx.setMessages(prev => prev.filter(m => m.id !== loadingMsg.id))
        ctx.setIsLoadingEnrichment(false)
        const errorMsg: Message = {
          id: `jd-enrichment-error-${Date.now()}`,
          role: 'assistant',
          content: '❌ Não consegui buscar as sugestões de mercado. Você pode continuar preenchendo manualmente ou tentar novamente.',
          timestamp: new Date()
        }
        ctx.setMessages(prev => [...prev, errorMsg])
      })
      return true
    }

    const transitionMsg: Message = {
      id: `stage-transition-${Date.now()}`,
      role: 'assistant',
      content: getStageTransitionMessage(nextStage, {}),
      timestamp: new Date(),
    }
    ctx.setMessages(prev => [...prev, transitionMsg])
    ctx.setCurrentStage(nextStage as WizardStage)
    ctx.setAwaitingStageAdvanceConfirmation(null)
    if (nextStage === 'salary') {
      setTimeout(() => {
        const parecerData = ctx.generateParecerData()
        const parecerMsg: Message = {
          id: `parecer-lia-${Date.now()}`,
          role: 'assistant',
          content: `Preparei uma análise completa da sua vaga antes de configurar a remuneração.`,
          timestamp: new Date(),
          messageType: 'parecer-lia',
          parecerData
        }
        ctx.setMessages(prev => [...prev, parecerMsg])
      }, 500)
    }
    return true
  }

  ctx.setAwaitingStageAdvanceConfirmation(null)
  return false
}

export async function handleFastTrackSuggestions(
  content: string,
  ctx: SendMessageHandlersContext
): Promise<boolean> {
  if (!ctx.isInJobCreationMode || !ctx.fastTrack.hasSuggestions) return false
  const lowerContent = content.toLowerCase().trim()

  const numberMatch = lowerContent.match(/\b([1-5])\b|primeira|segunda|terceira|quarta|quinta/)
  const hasExplicitSelection = numberMatch !== null

  const affirmativePatterns = [
    'sim', 'usa', 'usar', 'ok', 'vamos', 'pode ser', 'pode', 'essa', 'essa mesmo',
    'top', 'bora', 'beleza', 'perfeito', 'ótimo', 'legal', 'certo', 'fechou'
  ]
  const negativePatterns = [
    'não', 'nao', 'zero', 'nova', 'novo', 'criar', 'comecar', 'começar',
    'do zero', 'outra', 'diferente', 'prefiro não'
  ]

  const isAffirmative = affirmativePatterns.some(p => lowerContent.includes(p))
  const isNegative = negativePatterns.some(p => lowerContent.includes(p))

  if ((isAffirmative || hasExplicitSelection) && !isNegative) {
    if (ctx.awaitingFastTrackSelection && !numberMatch) {
      const reaskMessage: Message = {
        id: `fasttrack-reask-${Date.now()}`,
        role: 'assistant',
        content: 'Qual das vagas você quer usar? Diga o número (1, 2, 3...) ou "primeira", "segunda", etc.',
        timestamp: new Date(),
      }
      ctx.setMessages(prev => [...prev, reaskMessage])
      return true
    }

    if (ctx.fastTrack.suggestions.length > 1 && !numberMatch && !ctx.fastTrack.selectedJob) {
      const clarifyMessage: Message = {
        id: `fasttrack-clarify-${Date.now()}`,
        role: 'assistant',
        content: `Tenho ${ctx.fastTrack.suggestions.length} vagas similares. Qual você quer usar?\n\n${ctx.fastTrack.suggestions.slice(0, 5).map((s, i) => `${i + 1}. ${s.job_title}${s.department ? ` (${s.department})` : ''} - ${Math.round(s.similarity_score * 100)}% similar`).join('\n')}\n\nDiga o número ou "primeira", "segunda", etc.`,
        timestamp: new Date(),
      }
      ctx.setMessages(prev => [...prev, clarifyMessage])
      ctx.setAwaitingFastTrackSelection(true)
      return true
    }

    let jobToApply: FastTrackSuggestion | null = null
    if (numberMatch) {
      const indexMap: Record<string, number> = {
        '1': 0, 'primeira': 0, '2': 1, 'segunda': 1, '3': 2, 'terceira': 2,
        '4': 3, 'quarta': 3, '5': 4, 'quinta': 4
      }
      const index = indexMap[numberMatch[0].toLowerCase()] ?? 0
      if (index < ctx.fastTrack.suggestions.length) jobToApply = ctx.fastTrack.suggestions[index]
    } else if (ctx.fastTrack.selectedJob) {
      jobToApply = ctx.fastTrack.selectedJob
    } else if (ctx.fastTrack.suggestions.length === 1) {
      jobToApply = ctx.fastTrack.suggestions[0]
    }

    if (!jobToApply) return true

    let fastTrackData: FastTrackJobData | null = null
    try {
      fastTrackData = await ctx.fastTrack.applyFastTrack(jobToApply)
    } catch {
      ctx.setAwaitingFastTrackSelection(false)
      const errorMessage: Message = {
        id: `fasttrack-error-${Date.now()}`,
        role: 'assistant',
        content: 'Ops! Tive um problema ao aplicar os dados. Quer tentar novamente ou criar do zero?',
        timestamp: new Date(),
      }
      ctx.setMessages(prev => [...prev, errorMessage])
      return true
    }

    if (fastTrackData) {
      ctx.setBasicInfoFields({
        cargo: fastTrackData.basicInfo.cargo || '',
        area: fastTrackData.basicInfo.area || '',
        gestor: fastTrackData.basicInfo.gestor || '',
        localidade: fastTrackData.basicInfo.localidade || '',
        modeloTrabalho: fastTrackData.basicInfo.modeloTrabalho || '',
        tipoContrato: fastTrackData.basicInfo.tipoContrato || '',
      })
      ctx.setTechnicalSkills(fastTrackData.technicalSkills)
      ctx.setBehavioralCompetencies(fastTrackData.behavioralCompetencies)
      ctx.setSalaryInfo({
        minSalary: fastTrackData.salaryInfo.minSalary || '',
        maxSalary: fastTrackData.salaryInfo.maxSalary || '',
        minBonus: fastTrackData.salaryInfo.minBonus || '',
        maxBonus: fastTrackData.salaryInfo.maxBonus || '',
        bonusCriteria: fastTrackData.salaryInfo.bonusCriteria || '',
        benefits: fastTrackData.salaryInfo.benefits || [],
      })
      if (fastTrackData.wsiQuestions.length > 0) {
        ctx.setWsiCandidates(fastTrackData.wsiQuestions.map(q => ({
          ...q, selected: true, batch: 0, isWSI: true,
        })))
      }
      if (fastTrackData.generatedDescription) ctx.setGeneratedJobDescription(fastTrackData.generatedDescription)
      ctx.setDetectedCriteria(prev => ({ ...prev, ...fastTrackData.detectedCriteria }))
      ctx.setWizardFastTrackSourceJobId(fastTrackData.sourceJobId)
      ctx.setFastTrackOriginalCompetencies({
        technicalSkillNames: fastTrackData.technicalSkills.map(s => s.name.toLowerCase()),
        behavioralCompetencyNames: fastTrackData.behavioralCompetencies.map(c => c.name.toLowerCase())
      })
      ctx.setWsiRegenerationPrompted(false)
      ctx.setAwaitingFastTrackSelection(false)
      ctx.setFastTrackAppliedData({
        gestor: fastTrackData.basicInfo.gestor || '',
        localidade: fastTrackData.basicInfo.localidade || '',
        sourceJobTitle: jobToApply.job_title || ''
      })
      ctx.setAwaitingSensitiveFieldsConfirmation(true)
      ctx.analytics.trackSuggestion('fast_track_accepted', true)

      const localidadeInfo = fastTrackData.basicInfo.localidade
        ? `A localização continua sendo **${fastTrackData.basicInfo.localidade}**?`
        : 'Qual será a localidade da vaga?'
      const sensitiveFieldsMessage: Message = {
        id: `fasttrack-sensitive-${Date.now()}`,
        role: 'assistant',
        content: `Copiei todos os dados da vaga "${jobToApply.job_title}"! Só preciso confirmar alguns detalhes:\n\n1. **Quem é o gestor** responsável por esta vaga?\n2. ${localidadeInfo}\n3. **Essa vaga é afirmativa** para algum grupo (PcD, mulheres, pessoas negras, LGBTQ+, 50+)?`,
        timestamp: new Date(),
      }
      ctx.setMessages(prev => [...prev, sensitiveFieldsMessage])
      ctx.setIsPanelOpen(true)
    } else {
      ctx.setAwaitingFastTrackSelection(false)
      const errorMessage: Message = {
        id: `fasttrack-null-${Date.now()}`,
        role: 'assistant',
        content: 'Não consegui carregar os dados dessa vaga. Quer tentar outra ou criar do zero?',
        timestamp: new Date(),
      }
      ctx.setMessages(prev => [...prev, errorMessage])
    }
    return true
  }

  if (isNegative) {
    ctx.fastTrack.clearSuggestions()
    ctx.setFastTrackMessageSent(false)
    ctx.setAwaitingFastTrackSelection(false)
    ctx.analytics.trackSuggestion('fast_track_rejected', false)
    const liaMessage: Message = {
      id: `fasttrack-declined-${Date.now()}`,
      role: 'assistant',
      content: 'Tudo bem! Vamos criar uma nova vaga do zero. Me conta mais sobre a vaga que você precisa.',
      timestamp: new Date(),
    }
    ctx.setMessages(prev => [...prev, liaMessage])
    return true
  }

  return false
}

export async function handleFastTrackFlow(
  content: string,
  ctx: SendMessageHandlersContext
): Promise<boolean> {
  if (!ctx.isInJobCreationMode || (ctx.wizardMode !== 'pre_wizard' && ctx.wizardMode !== 'fast_track')) return false

  const intent = ctx.detectFastTrackIntent(content)

  if (ctx.wizardMode === 'pre_wizard') {
    if (intent === 'fast_track') {
      ctx.setWizardMode('fast_track')
      ctx.setFastTrackState('collecting_criteria')
      ctx.setIsPanelOpen(false)
      const liaMessage: Message = {
        id: `lia-fasttrack-${Date.now()}`,
        role: 'assistant',
        content: '🚀 **Ótima escolha!** Vou buscar suas vagas anteriores.\n\nPara encontrar a vaga certa, me diga pelo menos 2 critérios:\n- Cargo (ex: "Desenvolvedor Python")\n- Área ou departamento\n- Gestor responsável\n- Período aproximado\n\n**Exemplo:** "Desenvolvedor Python da equipe de dados do João"',
        timestamp: new Date()
      }
      ctx.setMessages(prev => [...prev, liaMessage])
      return true
    }

    if (intent === 'from_scratch') {
      ctx.setWizardMode('create_from_scratch')
      ctx.setIsPanelOpen(true)
      if (ctx.fastTrackSuggestionsShownTracked) ctx.analytics.trackSuggestion('fast_track_rejected', false)
      const liaMessage: Message = {
        id: `lia-scratch-${Date.now()}`,
        role: 'assistant',
        content: FROM_SCRATCH_ORIENTATION_MESSAGE,
        timestamp: new Date()
      }
      ctx.setMessages(prev => [...prev, liaMessage])
      return true
    }

    ctx.setIsLoading(true)
    try {
      const conversationalResponse = await getConversationalResponse({
        message: content,
        mode: 'job_creation',
        context: 'pre_wizard'
      })
      if (conversationalResponse.suggested_action === 'from_scratch') {
        ctx.setWizardMode('create_from_scratch')
        ctx.setIsPanelOpen(true)
        if (ctx.fastTrackSuggestionsShownTracked) ctx.analytics.trackSuggestion('fast_track_rejected', false)
        const liaMessage: Message = {
          id: `lia-scratch-ai-${Date.now()}`,
          role: 'assistant',
          content: FROM_SCRATCH_ORIENTATION_MESSAGE,
          timestamp: new Date()
        }
        ctx.setMessages(prev => [...prev, liaMessage])
        ctx.setIsLoading(false)
        return true
      }
      if (conversationalResponse.suggested_action === 'fast_track') {
        ctx.setWizardMode('fast_track')
        ctx.setFastTrackState('collecting_criteria')
        ctx.setIsPanelOpen(false)
        const liaMessage: Message = {
          id: `lia-fasttrack-ai-${Date.now()}`,
          role: 'assistant',
          content: '🚀 **Ótima escolha!** Vou buscar suas vagas anteriores.\n\nPara encontrar a vaga certa, me diga pelo menos 2 critérios:\n- Cargo (ex: "Desenvolvedor Python")\n- Área ou departamento\n- Gestor responsável\n- Período aproximado\n\n**Exemplo:** "Desenvolvedor Python da equipe de dados do João"',
          timestamp: new Date()
        }
        ctx.setMessages(prev => [...prev, liaMessage])
        ctx.setIsLoading(false)
        return true
      }
      const liaMessage: Message = {
        id: `lia-conversational-${Date.now()}`,
        role: 'assistant',
        content: conversationalResponse.response,
        timestamp: new Date()
      }
      ctx.setMessages(prev => [...prev, liaMessage])
    } catch {
      const liaMessage: Message = {
        id: `lia-guidance-fallback-${Date.now()}`,
        role: 'assistant',
        content: 'Sou a LIA, sua assistente de recrutamento! Aqui posso te ajudar a:\n\n• **Criar uma nova vaga** do zero com toda inteligência da plataforma\n• **Reutilizar uma vaga anterior** para publicar rapidamente\n\nComo gostaria de começar?',
        timestamp: new Date()
      }
      ctx.setMessages(prev => [...prev, liaMessage])
    } finally {
      ctx.setIsLoading(false)
    }
    return true
  }

  if (intent === 'confirm' && ctx.fastTrackState === 'reviewing') {
    await ctx.handleFastTrackPublish()
    return true
  }
  if (intent === 'adjust' && (ctx.fastTrackState === 'reviewing' || ctx.fastTrackState === 'adjusting')) {
    const adjustments = ctx.parseFastTrackAdjustment(content)
    if (adjustments) {
      ctx.setFastTrackAdjustments(prev => ({ ...prev, ...adjustments }))
      ctx.setFastTrackState('adjusting')
      if (ctx.fastTrackSelectedVacancy) {
        const updatedVacancy: VacancyFullDetails = {
          ...ctx.fastTrackSelectedVacancy,
          salary_range: {
            ...ctx.fastTrackSelectedVacancy.salary_range,
            min: adjustments.salary_min ?? ctx.fastTrackSelectedVacancy.salary_range?.min,
            max: adjustments.salary_max ?? ctx.fastTrackSelectedVacancy.salary_range?.max,
          },
          work_model: adjustments.work_model ?? ctx.fastTrackSelectedVacancy.work_model,
          location: adjustments.location ?? ctx.fastTrackSelectedVacancy.location,
        }
        ctx.setFastTrackSelectedVacancy(updatedVacancy)
        const salaryMin = updatedVacancy.salary_range?.min?.toLocaleString('pt-BR') ?? '–'
        const salaryMax = updatedVacancy.salary_range?.max?.toLocaleString('pt-BR') ?? '–'
        const liaMessage: Message = {
          id: `lia-adjust-${Date.now()}`,
          role: 'assistant',
          content: `✅ **Ajuste aplicado!**\n\nAtualizei os valores conforme solicitado. Revise o resumo atualizado:\n\n• Salário: R$ ${salaryMin} - R$ ${salaryMax}\n• Modelo: ${updatedVacancy.work_model}\n• Local: ${updatedVacancy.location}\n\nSe quiser fazer mais ajustes, me diga. Quando estiver pronto, digite **"confirmar"** para publicar.`,
          timestamp: new Date()
        }
        ctx.setMessages(prev => [...prev, liaMessage])
        ctx.setFastTrackState('reviewing')
      }
    } else {
      const liaMessage: Message = {
        id: `lia-adjust-error-${Date.now()}`,
        role: 'assistant',
        content: 'Não consegui entender o ajuste solicitado. Por favor, seja mais específico.\n\n**Exemplos:**\n• "salário para 15 a 20k"\n• "modelo híbrido"\n• "local para São Paulo"',
        timestamp: new Date()
      }
      ctx.setMessages(prev => [...prev, liaMessage])
    }
    return true
  }
  if (intent === 'select' && ctx.fastTrackState === 'selecting') {
    const numMatch = content.match(/(\d+)/)
    const numberWords: Record<string, number> = { 'um': 1, 'dois': 2, 'três': 3, 'quatro': 4, 'cinco': 5, 'seis': 6, 'sete': 7, 'oito': 8, 'nove': 9, 'dez': 10 }
    let index = -1
    if (numMatch) {
      index = parseInt(numMatch[1]) - 1
    } else {
      const word = content.toLowerCase().trim()
      if (numberWords[word]) index = numberWords[word] - 1
    }
    if (index >= 0 && index < ctx.fastTrackSearchResults.length) {
      const selectedVacancy = ctx.fastTrackSearchResults[index]
      ctx.setFastTrackState('reviewing')
      await ctx.handleFastTrackVacancySelect(selectedVacancy.id)
    } else {
      const liaMessage: Message = {
        id: `lia-select-error-${Date.now()}`,
        role: 'assistant',
        content: `Número inválido. Por favor, escolha um número de 1 a ${ctx.fastTrackSearchResults.length}.`,
        timestamp: new Date()
      }
      ctx.setMessages(prev => [...prev, liaMessage])
    }
    return true
  }
  if (intent === 'criteria' || ctx.fastTrackState === 'collecting_criteria') {
    const criteria: VacancySearchCriteria = {}
    const wantsToListAll = /(?:lista|listar|mostrar|ver|quais|todas|exibir|apresentar)\s*(?:as|as\s+vagas|vagas|anteriores|recentes|últimas|existentes)?/i.test(content)
    const titleMatch = content.match(/(?:desenvolvedor|analista|gerente|coordenador|engenheiro|designer|product|ux|ui|frontend|backend|fullstack|devops|data|cientista|tech lead|architect)[^\s,.]*/gi)
    if (titleMatch) criteria.title = titleMatch[0]
    const managerMatch = content.match(/(?:do|da|equipe do|equipe da|gestor)\s+([A-Z][a-zà-ú]+(?:\s+[A-Z][a-zà-ú]+)?)/i)
    if (managerMatch) criteria.manager = managerMatch[1]
    const deptMatch = content.match(/(?:área|departamento|setor|time|equipe)\s+(?:de\s+)?([A-Za-zà-ú\s]+)/i)
    if (deptMatch) criteria.department = deptMatch[1].trim()
    ctx.setFastTrackSearchCriteria(criteria)

    if (Object.keys(criteria).length > 0 || wantsToListAll) {
      const liaMessage: Message = {
        id: `lia-searching-${Date.now()}`,
        role: 'assistant',
        content: wantsToListAll && Object.keys(criteria).length === 0
          ? '🔍 Buscando suas vagas mais recentes...'
          : '🔍 Buscando vagas anteriores...',
        timestamp: new Date(),
        isProcessing: true,
        processingState: 'searching'
      }
      ctx.setMessages(prev => [...prev, liaMessage])
      await ctx.handleFastTrackSearch(criteria)
      ctx.setMessages(prev => prev.filter(m => m.id !== liaMessage.id))
    } else {
      const liaMessage: Message = {
        id: `lia-criteria-help-${Date.now()}`,
        role: 'assistant',
        content: 'Preciso de mais informações para buscar. Me diga:\n\n• **Cargo** - "Desenvolvedor Python", "Analista de Dados"\n• **Gestor** - "equipe do João", "área do Ricardo"\n• **Departamento** - "área de tecnologia", "time de produto"\n\nOu digite **"listar todas"** para ver as vagas mais recentes.',
        timestamp: new Date()
      }
      ctx.setMessages(prev => [...prev, liaMessage])
    }
    return true
  }
  if (intent === 'from_scratch') {
    ctx.setWizardMode('create_from_scratch')
    ctx.setIsPanelOpen(true)
    const liaMessage: Message = {
      id: `lia-switch-${Date.now()}`,
      role: 'assistant',
      content: FROM_SCRATCH_ORIENTATION_MESSAGE,
      timestamp: new Date()
    }
    ctx.setMessages(prev => [...prev, liaMessage])
    return true
  }

  return false
}

export async function handleCompensationMessage(
  content: string,
  ctx: SendMessageHandlersContext
): Promise<boolean> {
  const lowerContent = content.toLowerCase().trim()
  const hasCompensationMessage = ctx.messages.some(m => m.messageType === 'compensation')
  if (!hasCompensationMessage) return false

  const thinkingId = `thinking-interpret-${Date.now()}`
  const thinkingMessage: Message = {
    id: thinkingId,
    role: 'assistant',
    content: '',
    timestamp: new Date(),
    processingState: 'thinking' as const
  }
  ctx.setMessages(prev => [...prev, thinkingMessage])

  try {
    const detectedCriteriaRecord = ctx.detectedCriteria as unknown as Record<string, unknown>
    const interpretation = await interpretMessage({
      message: content,
      current_stage: ctx.currentStage,
      context: {
        filled_fields: Object.keys(ctx.detectedCriteria).filter(k => detectedCriteriaRecord[k]),
        has_compensation: true,
        salary_min: ctx.salaryInfo.minSalary,
        salary_max: ctx.salaryInfo.maxSalary
      }
    })

    ctx.setMessages(prev => prev.filter(m => m.id !== thinkingId))

    const MIN_CONFIDENCE = 0.65
    const isHighConfidence = interpretation.confidence >= MIN_CONFIDENCE

    if (isHighConfidence && (interpretation.action === 'confirm' || interpretation.action === 'advance_stage' || interpretation.should_advance)) {
      const entities = interpretation.extracted_entities as Record<string, unknown> | undefined
      if (entities && Object.keys(entities).length > 0) {
        if (entities.salario_min) {
          ctx.setSalaryInfo(prev => ({ ...prev, minSalary: String(entities.salario_min) }))
        }
        if (entities.salario_max) {
          ctx.setSalaryInfo(prev => ({ ...prev, maxSalary: String(entities.salario_max) }))
        }
      }
      const minSal = parseInt(ctx.salaryInfo.minSalary) || 0
      const maxSal = parseInt(ctx.salaryInfo.maxSalary) || 0
      if (!(minSal > 0 && maxSal > 0)) {
        const askSalaryMsg: Message = {
          id: `ask-salary-${Date.now()}`,
          role: 'assistant',
          content: '💰 Antes de avançar, preciso confirmar a faixa salarial. Qual é o salário mínimo e máximo para esta vaga?',
          timestamp: new Date()
        }
        ctx.setMessages(prev => [...prev, askSalaryMsg])
        return true
      }
      if (minSal > maxSal) {
        const warningMsg: Message = {
          id: `salary-order-warning-${Date.now()}`,
          role: 'assistant',
          content: '⚠️ O salário mínimo não pode ser maior que o máximo. Por favor, corrija os valores.',
          timestamp: new Date()
        }
        ctx.setMessages(prev => [...prev, warningMsg])
        return true
      }
      ctx.setMessages(prev => prev.filter(m => m.messageType !== 'compensation'))
      ctx.setCompensationAnalysis(null)
      const confirmMessage: Message = {
        id: `confirm-compensation-${Date.now()}`,
        role: 'assistant',
        content: interpretation.lia_response || '✅ **Valores de remuneração confirmados!**\n\nAvançando para a próxima etapa...',
        timestamp: new Date()
      }
      ctx.setMessages(prev => [...prev, confirmMessage])
      setTimeout(() => { ctx.goToNextStage() }, 1500)
      return true
    }

    if (isHighConfidence && (interpretation.action === 'update_field' || interpretation.action === 'provide_data')) {
      const ents = interpretation.extracted_entities as Record<string, unknown> | undefined
      if (ents) {
        const newMin = ents.salario_min as number | undefined
        const newMax = ents.salario_max as number | undefined
        if (newMin || newMax) {
          const minVal = newMin || parseInt(ctx.salaryInfo.minSalary) || 0
          const maxVal = newMax || parseInt(ctx.salaryInfo.maxSalary) || 0
          if (minVal > 0 && maxVal > 0 && minVal > maxVal) {
            const warningMessage: Message = {
              id: `salary-warning-${Date.now()}`,
              role: 'assistant',
              content: '⚠️ O salário mínimo não pode ser maior que o máximo. Por favor, informe os valores corretos.',
              timestamp: new Date()
            }
            ctx.setMessages(prev => [...prev, warningMessage])
            return true
          }
          if (newMin) ctx.setSalaryInfo(prev => ({ ...prev, minSalary: newMin.toString() }))
          if (newMax) ctx.setSalaryInfo(prev => ({ ...prev, maxSalary: newMax.toString() }))
          ctx.setMessages(prev => prev.filter(m => m.messageType !== 'compensation'))
          ctx.setCompensationAnalysis(null)
          const formatCurrency = (value: number) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', minimumFractionDigits: 0 }).format(value)
          const updateMessage: Message = {
            id: `update-salary-${Date.now()}`,
            role: 'assistant',
            content: `✅ **Valores atualizados!**\n\n• Mínimo: ${formatCurrency(minVal)}\n• Máximo: ${formatCurrency(maxVal)}\n\nVocê pode confirmar ou ajustar novamente.`,
            timestamp: new Date()
          }
          ctx.setMessages(prev => [...prev, updateMessage])
          return true
        }
      }
    }

    if (interpretation.action === 'reject') {
      const rejectMessage: Message = {
        id: `reject-${Date.now()}`,
        role: 'assistant',
        content: interpretation.lia_response || 'Entendido. O que você gostaria de ajustar?',
        timestamp: new Date()
      }
      ctx.setMessages(prev => [...prev, rejectMessage])
      return true
    }

    if (interpretation.action === 'help') {
      const helpMessage: Message = {
        id: `help-${Date.now()}`,
        role: 'assistant',
        content: interpretation.lia_response || '💡 **Ajuda - Etapa de Remuneração**\n\nVocê pode:\n• **Confirmar** os valores atuais\n• **Aceitar sugestões** de mercado\n• **Ajustar** para novos valores (ex: "quero salário de 10 a 15 mil")\n• Pedir para **avançar** para próxima etapa',
        timestamp: new Date()
      }
      ctx.setMessages(prev => [...prev, helpMessage])
      return true
    }

    if (interpretation.clarification_needed && interpretation.clarification_question) {
      const clarifyMessage: Message = {
        id: `clarify-${Date.now()}`,
        role: 'assistant',
        content: interpretation.clarification_question,
        timestamp: new Date()
      }
      ctx.setMessages(prev => [...prev, clarifyMessage])
      return true
    }

  } catch {
    ctx.setMessages(prev => prev.filter(m => m.id !== thinkingId))
  }

  const isConfirmCommand = lowerContent === 'confirmar' || lowerContent.includes('confirmo') ||
    lowerContent.includes('manter valores') || lowerContent.includes('manter atual') ||
    lowerContent.includes('próximo') || lowerContent.includes('proximo') ||
    lowerContent.includes('continuar') || lowerContent.includes('avançar') ||
    lowerContent.includes('avancar') || lowerContent.includes('próximo passo') ||
    lowerContent.includes('proximo passo') || lowerContent.includes('prosseguir') ||
    lowerContent.includes('vamos para') || lowerContent.includes('pode avançar') ||
    lowerContent.includes('ok') || lowerContent === 'sim' || lowerContent === 'ok'

  if (isConfirmCommand) {
    const minSal = parseInt(ctx.salaryInfo.minSalary) || 0
    const maxSal = parseInt(ctx.salaryInfo.maxSalary) || 0
    if (!(minSal > 0 && maxSal > 0)) {
      const askSalaryMsg: Message = {
        id: `ask-salary-fallback-${Date.now()}`,
        role: 'assistant',
        content: '💰 Antes de continuar, preciso da faixa salarial completa. Qual é o salário mínimo e máximo para esta vaga?',
        timestamp: new Date()
      }
      ctx.setMessages(prev => [...prev, askSalaryMsg])
      return true
    }
    if (minSal > maxSal) {
      const warningMsg: Message = {
        id: `salary-order-fallback-${Date.now()}`,
        role: 'assistant',
        content: '⚠️ O salário mínimo não pode ser maior que o máximo. Por favor, corrija os valores.',
        timestamp: new Date()
      }
      ctx.setMessages(prev => [...prev, warningMsg])
      return true
    }
    ctx.setMessages(prev => prev.filter(m => m.messageType !== 'compensation'))
    ctx.setCompensationAnalysis(null)
    const confirmMessage: Message = {
      id: `confirm-compensation-fallback-${Date.now()}`,
      role: 'assistant',
      content: '✅ **Valores de remuneração confirmados!**\n\nAvançando para a próxima etapa...',
      timestamp: new Date()
    }
    ctx.setMessages(prev => [...prev, confirmMessage])
    setTimeout(() => { ctx.goToNextStage() }, 1500)
    return true
  }

  if (lowerContent.includes('aceitar sugest') || lowerContent.includes('aplicar sugest')) {
    const analysis = ctx.compensationAnalysis
    if (analysis) {
      if (analysis.salary.suggestion) {
        ctx.setSalaryInfo(prev => ({
          ...prev,
          minSalary: analysis.salary.suggestion!.min.toString(),
          maxSalary: analysis.salary.suggestion!.max.toString()
        }))
      }
      if (analysis.bonus.suggestion) {
        ctx.setSalaryInfo(prev => ({
          ...prev,
          minBonus: analysis.bonus.suggestion!.toString(),
          maxBonus: analysis.bonus.suggestion!.toString()
        }))
      }
      if (analysis.benefits.missingFromStandard && analysis.benefits.missingFromStandard.length > 0) {
        const newBenefits = analysis.benefits.missingFromStandard.map(b => ({ id: b.id, name: b.name, value: b.value, enabled: true }))
        ctx.setSalaryInfo(prev => ({
          ...prev,
          benefits: [...prev.benefits, ...newBenefits.filter(nb => !prev.benefits.some(pb => pb.id === nb.id))]
        }))
      }
    }
    ctx.setMessages(prev => prev.filter(m => m.messageType !== 'compensation'))
    ctx.setCompensationAnalysis(null)
    const confirmMessage: Message = {
      id: `apply-suggestions-${Date.now()}`,
      role: 'assistant',
      content: '✅ **Sugestões aplicadas!**\n\nOs valores foram atualizados conforme as recomendações de mercado.',
      timestamp: new Date()
    }
    ctx.setMessages(prev => [...prev, confirmMessage])
    setTimeout(() => { ctx.goToNextStage() }, 1500)
    return true
  }

  const adjustMatch = lowerContent.match(/ajust(?:ar|e)?\s*(?:para)?\s*(?:r\$?\s*)?(\d+[\d.,]*)\s*(?:a|até|-|–|\/)\s*(?:r\$?\s*)?(\d+[\d.,]*)/i)
  if (adjustMatch) {
    const minValue = parseInt(adjustMatch[1].replace(/[.,]/g, ''))
    const maxValue = parseInt(adjustMatch[2].replace(/[.,]/g, ''))
    ctx.setSalaryInfo(prev => ({ ...prev, minSalary: minValue.toString(), maxSalary: maxValue.toString() }))
    ctx.setMessages(prev => prev.filter(m => m.messageType !== 'compensation'))
    ctx.setCompensationAnalysis(null)
    const formatCurrency = (value: number) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', minimumFractionDigits: 0 }).format(value)
    const confirmMessage: Message = {
      id: `adjust-salary-fallback-${Date.now()}`,
      role: 'assistant',
      content: `✅ **Faixa salarial atualizada!**\n\n• Mínimo: ${formatCurrency(minValue)}\n• Máximo: ${formatCurrency(maxValue)}\n\nVocê pode confirmar ou ajustar novamente.`,
      timestamp: new Date()
    }
    ctx.setMessages(prev => [...prev, confirmMessage])
    return true
  }

  return false
}

export function handleLocalCommands(
  content: string,
  ctx: SendMessageHandlersContext
): boolean {
  if (!ctx.isInJobCreationMode || ctx.wizardMode !== 'create_from_scratch' || ctx.currentStage === 'input-evaluation') return false

  const parsedCommand = parseCommand(content)

  if (parsedCommand.type === 'navigate') {
    const navCommand = parsedCommand as ParsedNavigationCommand
    const targetStage = navCommand.target
    const targetStageIndex = WIZARD_STAGES.findIndex(s => s.id === targetStage)
    const currentStageIndex = WIZARD_STAGES.findIndex(s => s.id === ctx.currentStage)

    if (targetStage === ctx.currentStage) {
      const alreadyHereMessage: Message = {
        id: `nav-already-here-${Date.now()}`,
        role: 'assistant',
        content: `Você já está na etapa de **${getStageLabel(targetStage)}**. Como posso ajudar?`,
        timestamp: new Date()
      }
      ctx.setMessages(prev => [...prev, alreadyHereMessage])
      return true
    }
    if (targetStageIndex < currentStageIndex) {
      ctx.setCurrentStage(targetStage)
      const navSuccessMessage: Message = {
        id: `nav-success-${Date.now()}`,
        role: 'assistant',
        content: `✅ Navegando para a etapa de **${getStageLabel(targetStage)}**.\n\nVocê pode revisar e ajustar os campos conforme necessário.`,
        timestamp: new Date()
      }
      ctx.setMessages(prev => [...prev, navSuccessMessage])
      return true
    }
    const stageConfig = WIZARD_STAGES.find(s => s.id === ctx.currentStage)
    if (stageConfig) {
      ctx.setCurrentStage(targetStage)
      const navForwardMessage: Message = {
        id: `nav-forward-${Date.now()}`,
        role: 'assistant',
        content: `✅ Navegando para a etapa de **${getStageLabel(targetStage)}**.\n\n💡 *Dica: Lembre-se de revisar as etapas anteriores antes de finalizar.*`,
        timestamp: new Date()
      }
      ctx.setMessages(prev => [...prev, navForwardMessage])
      return true
    }
  }

  if (parsedCommand.type === 'edit') {
    const editCommand = parsedCommand as ParsedEditCommand

    if (editCommand.field === 'salary' && editCommand.value) {
      const salaryResult = parseSalaryValue(String(editCommand.value))
      if (salaryResult.isValid) {
        const { updated, changes } = applySalaryUpdate(ctx.salaryInfo, salaryResult)
        if (updated.minSalary !== ctx.salaryInfo.minSalary) {
          ctx.trackFieldChange({ field: 'minSalary', oldValue: ctx.salaryInfo.minSalary, newValue: updated.minSalary, source: 'chat' })
        }
        if (updated.maxSalary !== ctx.salaryInfo.maxSalary) {
          ctx.trackFieldChange({ field: 'maxSalary', oldValue: ctx.salaryInfo.maxSalary, newValue: updated.maxSalary, source: 'chat' })
        }
        ctx.setSalaryInfo(updated)
        ctx.setMessages(prev => prev.filter(m => m.messageType !== 'compensation'))
        ctx.setCompensationAnalysis(null)
        const confirmMessage: Message = {
          id: `edit-salary-${Date.now()}`,
          role: 'assistant',
          content: `✅ **Salário atualizado!**\n\n${changes.length > 0 ? changes.join('\n') : `Faixa salarial definida: ${salaryResult.formatted}`}\n\n*Você pode confirmar ou ajustar novamente.*`,
          timestamp: new Date()
        }
        ctx.setMessages(prev => [...prev, confirmMessage])
        if (ctx.currentStage !== 'salary') ctx.setCurrentStage('salary')
        return true
      } else {
        const errorMessage: Message = {
          id: `edit-salary-error-${Date.now()}`,
          role: 'assistant',
          content: `❌ Não consegui entender o valor do salário. Por favor, use formatos como:\n• "15k" (para R$ 15.000)\n• "R$ 10.000 a R$ 15.000"\n• "10k a 15k"`,
          timestamp: new Date()
        }
        ctx.setMessages(prev => [...prev, errorMessage])
        return true
      }
    }

    if (editCommand.field === 'skill' && editCommand.value) {
      const skillName = String(editCommand.value)
      if (editCommand.action === 'add') {
        const result = addSkillIfNotExists(ctx.technicalSkills, skillName)
        if (result.added) {
          ctx.trackFieldChange({ field: 'technicalSkill', oldValue: null, newValue: { name: skillName }, source: 'chat' })
          ctx.setTechnicalSkills(result.skills)
        }
        const confirmMessage: Message = {
          id: `edit-skill-add-${Date.now()}`,
          role: 'assistant',
          content: result.added
            ? `✅ **Skill adicionada:** ${skillName}\n\n*A nova skill aparece no painel de competências.*`
            : `ℹ️ ${result.message}`,
          timestamp: new Date()
        }
        ctx.setMessages(prev => [...prev, confirmMessage])
        if (ctx.currentStage !== 'competencies') ctx.setCurrentStage('competencies')
        return true
      }
      if (editCommand.action === 'remove') {
        const result = removeSkillByName(ctx.technicalSkills, skillName)
        if (result.removed) {
          ctx.trackFieldChange({ field: 'technicalSkill', oldValue: { name: skillName }, newValue: null, source: 'chat' })
          ctx.setTechnicalSkills(result.skills)
        }
        const confirmMessage: Message = {
          id: `edit-skill-remove-${Date.now()}`,
          role: 'assistant',
          content: result.removed
            ? `✅ **Skill removida:** ${skillName}`
            : `ℹ️ ${result.message}`,
          timestamp: new Date()
        }
        ctx.setMessages(prev => [...prev, confirmMessage])
        if (ctx.currentStage !== 'competencies') ctx.setCurrentStage('competencies')
        return true
      }
    }
  }

  return false
}
