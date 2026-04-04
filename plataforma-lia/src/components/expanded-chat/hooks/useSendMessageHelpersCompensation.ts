import { CURRENCY_SYMBOL } from "@/lib/pricing"
import type { SendMessageHandlersContext } from './useSendMessageHandlers'
import type { Message } from '../types'
import type { ParsedNavigationCommand, ParsedEditCommand } from '../utils'
import {
  WIZARD_STAGES,
} from '../index'
import {
  interpretMessage,
} from '@/services/lia-api'
import { parseSalaryValue, applySalaryUpdate, addSkillIfNotExists, removeSkillByName, parseCommand, getStageLabel } from '../utils'

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
          content: `❌ Não consegui entender o valor do salário. Por favor, use formatos como:\n• "15k" (para ${CURRENCY_SYMBOL} 15.000)\n• "${CURRENCY_SYMBOL} 10.000 a ${CURRENCY_SYMBOL} 15.000"\n• "10k a 15k"`,
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
