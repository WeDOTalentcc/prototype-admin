import { CURRENCY_SYMBOL } from "@/lib/pricing"
import type { SendMessageHandlersContext } from './useSendMessageHandlers'
import type { Message } from '../types'
import type { VacancyFullDetails } from '@/components/job-creation/vacancy-full-summary'
import type { VacancySearchCriteria } from '@/services/lia-api'
import type { FastTrackSuggestion, FastTrackJobData } from '@/hooks/recruitment/useFastTrack'
import {
  FROM_SCRATCH_ORIENTATION_MESSAGE,
} from '../index'
import {
  getConversationalResponse,
} from '@/services/lia-api'

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
        context: 'pre_wizard',
        conversation_id: ctx.conversationId || undefined,
      })

      // Persist the conversation_id returned by the backend (auto-created if absent)
      if (conversationalResponse.conversation_id && !ctx.conversationId) {
        ctx.setConversationId(conversationalResponse.conversation_id)
      }
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
      if (
        conversationalResponse.suggested_action === 'resume_draft' ||
        conversationalResponse.suggested_action === 'offer_resume_draft'
      ) {
        const liaMessage: Message = {
          id: `lia-resume-draft-${Date.now()}`,
          role: 'assistant',
          content: conversationalResponse.response,
          timestamp: new Date()
        }
        ctx.setMessages(prev => [...prev, liaMessage])

        // Hydrate pending draft state from the response's active_draft so user can continue
        const activeDraft = conversationalResponse.active_draft
        if (activeDraft) {
          const ts = Date.now()
          const mappedDraftData = {
            currentStage: activeDraft.current_step || 'input-evaluation',
            basicInfoFields: {
              jobTitle: activeDraft.job_title || '',
              department: activeDraft.department || '',
              seniority: activeDraft.seniority || '',
              locality: activeDraft.location || '',
              workModel: activeDraft.work_model || '',
              employmentType: activeDraft.employment_type || '',
              manager: activeDraft.manager || '',
              isAffirmative: activeDraft.is_affirmative || false,
            },
            technicalSkills: (activeDraft.skills || []).map((name: string, idx: number) => ({
              id: `skill-${ts}-${idx}`,
              name,
              level: 'Avançado' as const,
              required: idx < 3,
              category: 'tool' as const,
              weight: idx < 3 ? 3 : 2,
            })),
            behavioralCompetencies: (activeDraft.behavioral_competencies || []).map((bc: unknown, idx: number) => {
              const b = bc as Record<string, unknown>
              return {
                id: (b.id as string) || `comp-${ts}-${idx}`,
                name: (b.name as string) || '',
                weight: (b.weight as number) ?? 2,
                justification: (b.justification as string) || '',
                enabled: b.enabled !== false,
              }
            }),
            salaryInfo: {
              minSalary: String(activeDraft.salary_min ?? ''),
              maxSalary: String(activeDraft.salary_max ?? ''),
              minBonus: '',
              maxBonus: '',
              bonusCriteria: '',
              benefits: (activeDraft.benefits || []).map((b: unknown, i: number) =>
                typeof b === 'string'
                  ? { id: `benefit-${ts}-${i}`, name: b, enabled: true }
                  : { id: `benefit-${ts}-${i}`, name: String(b), enabled: true }
              ),
            },
          }
          ctx.setPendingDraftData(mappedDraftData)
          ctx.setAwaitingDraftChoice(true)
          ctx.setInternalJobCreationMode(true)
        }

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
        content: 'Estou com dificuldade para processar essa solicitação no momento. Pode tentar novamente em alguns segundos?',
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
          content: `✅ **Ajuste aplicado!**\n\nAtualizei os valores conforme solicitado. Revise o resumo atualizado:\n\n• Salário: ${CURRENCY_SYMBOL} ${salaryMin} - ${CURRENCY_SYMBOL} ${salaryMax}\n• Modelo: ${updatedVacancy.work_model}\n• Local: ${updatedVacancy.location}\n\nSe quiser fazer mais ajustes, me diga. Quando estiver pronto, digite **"confirmar"** para publicar.`,
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
