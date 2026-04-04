import type { SendMessageHandlersContext } from './useSendMessageHandlers'
import type { Message } from '../types'
import type { WizardStage } from '../config'
import {
  getStageTransitionMessage,
} from '../index'
import {
  orchestrateWizardMessage,
} from '@/services/lia-api'

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
