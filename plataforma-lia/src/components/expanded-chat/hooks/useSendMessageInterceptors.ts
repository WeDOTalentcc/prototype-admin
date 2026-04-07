"use client"

import type { Message } from "../types"
import type { SendMessageHandlersContext } from './useSendMessageHandlers'
import {
  WIZARD_STAGES,
} from "../index"
import {
  handleStageAdvanceConfirmation,
  handleFastTrackSuggestions,
  handleFastTrackFlow,
  handleCompensationMessage,
  handleLocalCommands,
} from './useSendMessageHelpers'
import { useMessageConfirmationHandlers } from './useMessageConfirmationHandlers'

export function useSendMessageInterceptors(ctx: SendMessageHandlersContext) {
  const {
    onOrchestratedMessage,
    messages,
    setMessages,
    setIsLoading,
    isTypingEffect,
    conversationId,
    user,
    currentStage,
    setCurrentStage,
    wizardMode,
    setWizardMode,
    isInJobCreationMode,
    awaitingStageAdvanceConfirmation,
    setAwaitingStageAdvanceConfirmation,
    awaitingDraftChoice,
    setAwaitingDraftChoice,
    awaitingCalibrationChoice,
    setAwaitingCalibrationChoice,
    activeToolConfirmationMessageId,
    setActiveToolConfirmationMessageId,
    awaitingWSIRegenerationConfirmation,
    setAwaitingWSIRegenerationConfirmation,
    awaitingSensitiveFieldsConfirmation,
    setAwaitingSensitiveFieldsConfirmation,
    pendingDraftData,
    setPendingDraftData,
    setHasAppliedRestoredDraft,
    applyPendingDraft,
    clearWizardDraft,
    calibrationComplete,
    setCalibrationComplete,
    approvedCandidates,
    rejectedCandidates,
    setIsPanelOpen,
    localCandidateCount,
    setShowCalibrationModal,
    fastTrackAppliedData,
    setFastTrackAppliedData,
    basicInfoFields,
    setBasicInfoFields,
    setDetectedCriteria,
    technicalSkills,
    setTechnicalSkills,
    behavioralCompetencies,
    setBehavioralCompetencies,
    salaryInfo,
    setSalaryInfo,
    wsiQuestions,
    setWsiQuestions,
    wsiCandidates,
    setWsiCandidates,
    setCompetencySuggestions,
    generatedJobDescription,
    setGeneratedJobDescription,
    setJobConfig,
    detectedCriteria,
    wizardFastTrackSourceJobId,
    contextSwitching,
    conversationMemory,
    analytics,
    toolCalling,
    learning,
  } = ctx

  const _handleContextSwitch = (content: string): void => {
    const detectedContext = contextSwitching.detectContextFromMessage(content)
    if (!detectedContext || detectedContext === contextSwitching.currentContext) return
    if (contextSwitching.isInWizardContext) {
      contextSwitching.saveWizardSnapshot({
        stage: currentStage,
        basicInfoFields: basicInfoFields as unknown as Record<string, unknown>,
        technicalSkills,
        behavioralCompetencies,
        salaryInfo: salaryInfo as unknown as Record<string, unknown>,
        wsiQuestions,
        detectedCriteria: detectedCriteria as unknown as Record<string, unknown>,
        generatedJobDescription,
        fastTrackSourceJobId: wizardFastTrackSourceJobId,
      })
    } else {
      contextSwitching.saveGeneralSnapshot({
        conversationId: conversationMemory.conversationId || conversationId,
        lastMessageIndex: messages.length,
      })
    }
    if (detectedContext === 'wizard') contextSwitching.switchToWizard()
    else if (detectedContext === 'fast_track') contextSwitching.switchToFastTrack()
    else if (detectedContext === 'general') contextSwitching.switchToGeneral()
  }

  const _handleStageAdvanceConfirmation = (content: string) => handleStageAdvanceConfirmation(content, ctx)

  const _handleDraftChoice = async (content: string): Promise<boolean> => {
    if (!awaitingDraftChoice) return false
    const lowerContent = content.toLowerCase().trim()

    if (lowerContent.includes('continuar') || lowerContent.includes('retomar') ||
        lowerContent.includes('prosseguir') || lowerContent.includes('sim')) {
      applyPendingDraft()
      const currentStageConfig = WIZARD_STAGES.find(s => s.id === pendingDraftData?.currentStage)
      const stageMessage = currentStageConfig?.liaMessage || 'Continuando de onde você parou...'
      const liaMessage: Message = {
        id: `lia-continue-draft-${Date.now()}`,
        role: 'assistant',
        content: `Perfeito! Vou retomar de onde você parou. 📋\n\n${stageMessage}`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, liaMessage])
      setIsPanelOpen(true)
      return true
    }

    if (lowerContent.includes('zero') || lowerContent.includes('nova') ||
        lowerContent.includes('novo') || lowerContent.includes('descartar') ||
        lowerContent.includes('limpar') || lowerContent.includes('recomeçar')) {
      clearWizardDraft()
      setPendingDraftData(null)
      setAwaitingDraftChoice(false)
      setHasAppliedRestoredDraft(true)
      setCurrentStage('input-evaluation')
      setBasicInfoFields({ cargo: '', area: '', gestor: '', localidade: '', modeloTrabalho: '', tipoContrato: '' })
      setSalaryInfo({ minSalary: '', maxSalary: '', minBonus: '', maxBonus: '', bonusCriteria: '', benefits: [] })
      setTechnicalSkills([])
      setBehavioralCompetencies([])
      setWsiCandidates([])
      setGeneratedJobDescription('')
      const liaMessage: Message = {
        id: `lia-fresh-start-${Date.now()}`,
        role: 'assistant',
        content: 'Perfeito! Vamos criar uma nova vaga do zero. 🆕\n\nMe conte sobre a posição que você precisa preencher. Pode descrever livremente - cargo, responsabilidades, requisitos, área, modelo de trabalho... Eu vou extrair as informações automaticamente.\n\n💡 **Dica:** Quanto mais detalhes você fornecer, mais precisa será a vaga gerada.',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, liaMessage])
      setIsPanelOpen(true)
      setWizardMode('create_from_scratch')
      return true
    }

    const clarifyMessage: Message = {
      id: `lia-clarify-${Date.now()}`,
      role: 'assistant',
      content: 'Não entendi sua escolha. Por favor, digite **"continuar"** para retomar o rascunho, ou **"começar do zero"** para descartar e criar uma nova vaga.',
      timestamp: new Date()
    }
    setMessages(prev => [...prev, clarifyMessage])
    return true
  }

  const _handleCalibrationChoice = async (content: string): Promise<boolean> => {
    if (!awaitingCalibrationChoice || currentStage !== 'search-calibration') return false
    const lowerContent = content.toLowerCase().trim()

    const calibratePatterns = [
      'calibrar', 'calibração', 'calibracao',
      'avaliar candidato', 'avaliar perfis',
      'mostrar candidato', 'mostra candidato', 'ver candidato', 'ver perfis',
      'quero calibrar', 'calibrar agora', 'mostrar perfis', 'avaliar agora'
    ]
    const skipPatterns = [
      'kanban', 'kbn', 'pular', 'direto', 'ir para', 'skip',
      'depois', 'mais tarde', 'funil', 'pipeline',
      'sem calibração', 'sem calibracao', 'calibrar depois',
      'ir pro kanban', 'manda pro funil', 'pode pular',
      'prefiro kanban', 'quero ir pro kanban', 'vai pro kanban',
      'aprendizado natural', 'aprender no kanban'
    ]

    const hasCalibrationIntent = calibratePatterns.some(p => lowerContent.includes(p))
    let hasSkipIntent = skipPatterns.some(p => lowerContent.includes(p))

    if ((lowerContent === 'não' || lowerContent === 'nao') && !hasCalibrationIntent) {
      hasSkipIntent = true
    }

    const explicitRejectCalibration = lowerContent.includes('não') && lowerContent.includes('calibr')
    const hasConflictingIntent = hasCalibrationIntent && hasSkipIntent

    if (hasConflictingIntent) {
      setAwaitingCalibrationChoice(true)
      const conflictClarifyMessage: Message = {
        id: `lia-clarify-conflict-${Date.now()}`,
        role: 'assistant',
        content: `Percebi que você mencionou calibração mas também parece querer deixar para depois. Para confirmar:\n\n• **"Calibrar agora"** - mostro 5 perfis para avaliar rapidamente\n• **"Ir pro kanban"** - adiciono candidatos e você avalia lá\n\nQual prefere?`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, conflictClarifyMessage])
      return true
    }

    if (hasSkipIntent || explicitRejectCalibration) {
      setAwaitingCalibrationChoice(false)
      const skipMessage: Message = {
        id: `lia-skip-calibration-${Date.now()}`,
        role: 'assistant',
        content: `Perfeito! Os candidatos já estão sendo adicionados ao Kanban da vaga. 🎯\n\n**Aprendizado Implícito Ativado:**\nQuando você mover candidatos no Kanban (aprovar → entrevista, reprovar → descartado), eu automaticamente aprendo suas preferências e ajusto as futuras sugestões.\n\n📊 **Candidatos encontrados:** ${localCandidateCount > 0 ? localCandidateCount : 'Buscando...'}\n\nClique no botão abaixo para ir ao Kanban da vaga.`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, skipMessage])
      setCalibrationComplete(true)
      return true
    }

    if (hasCalibrationIntent && !hasSkipIntent) {
      setAwaitingCalibrationChoice(false)
      const calibrateMessage: Message = {
        id: `lia-start-calibration-${Date.now()}`,
        role: 'assistant',
        content: `Ótimo! Vou te mostrar 5 perfis para você avaliar rapidamente. 🔍\n\nBasta indicar se cada candidato é **aderente** ou **não aderente** ao perfil da vaga.\n\nCarregando os primeiros perfis...`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, calibrateMessage])
      setShowCalibrationModal(true)
      return true
    }

    const ambiguousAffirmative = ['sim', 'ok', 'pode', 'vamos', 'bora', 'claro', 'beleza'].some(p => lowerContent === p || lowerContent.startsWith(p + ' '))
    if (ambiguousAffirmative) {
      const clarifyAmbiguousMessage: Message = {
        id: `lia-clarify-ambiguous-${Date.now()}`,
        role: 'assistant',
        content: `Ótimo! Só para confirmar, você quer:\n          \n• **"Calibrar"** - eu mostro 5 perfis para você avaliar rapidamente\n• **"Ir pro kanban"** - eu adiciono os candidatos e você avalia lá\n\nQual prefere?`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, clarifyAmbiguousMessage])
      return true
    }

    const clarifyCalibrationMessage: Message = {
      id: `lia-clarify-calibration-${Date.now()}`,
      role: 'assistant',
      content: 'Não entendi sua preferência. Você quer **"calibrar"** (avaliar 5 perfis) ou **"ir pro kanban"** (aprendizado natural)?',
      timestamp: new Date()
    }
    setMessages(prev => [...prev, clarifyCalibrationMessage])
    return true
  }

  const _handlePendingToolConfirmation = async (content: string): Promise<boolean> => {
    if (!toolCalling.hasPendingTool || !activeToolConfirmationMessageId) return false
    const lowerContent = content.toLowerCase().trim()

    const affirmativePatterns = ['sim', 'pode', 'ok', 'claro', 'confirmo', 'confirma', 'prossegue', 'prosseguir', 'fazer', 'execute', 'aceito', 'pode ser', 'beleza', 'manda', 'vai', 'bora']
    const negativePatterns = ['não', 'nao', 'cancela', 'cancelar', 'deixa', 'para', 'espera', 'aguarda', 'negativo', 'desisto']

    const isAffirmative = affirmativePatterns.some(p => lowerContent.includes(p))
    const isNegative = negativePatterns.some(p => lowerContent.includes(p))

    if (isAffirmative && !isNegative) {
      setIsLoading(true)
      try {
        const result = await toolCalling.confirmToolCall()
        const feedbackMessage: Message = {
          id: `tool-feedback-${Date.now()}`,
          role: 'assistant',
          content: result.success ? `✅ ${result.message}` : `❌ ${result.error || result.message}`,
          timestamp: new Date(),
          messageType: 'tool-execution-feedback',
          toolExecutionResult: result,
        }
        setMessages(prev => [...prev, feedbackMessage])
        setActiveToolConfirmationMessageId(null)
        if (result.success) {
          const followUpMessage: Message = {
            id: `tool-followup-${Date.now()}`,
            role: 'assistant',
            content: 'Posso ajudar com mais alguma coisa?',
            timestamp: new Date(),
          }
          setTimeout(() => {
            setMessages(prev => [...prev, followUpMessage])
          }, 500)
        }
      } catch (error) {
        const errorMessage: Message = {
          id: `tool-error-${Date.now()}`,
          role: 'assistant',
          content: 'Tive um problema ao executar a ação. Por favor, tente novamente.',
          timestamp: new Date(),
        }
        setMessages(prev => [...prev, errorMessage])
        setActiveToolConfirmationMessageId(null)
      } finally {
        setIsLoading(false)
      }
      return true
    }

    if (isNegative) {
      toolCalling.cancelToolCall()
      setActiveToolConfirmationMessageId(null)
      const cancelMessage: Message = {
        id: `tool-cancel-${Date.now()}`,
        role: 'assistant',
        content: 'Tudo bem, cancelei a ação. Se precisar de algo mais, é só me avisar!',
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, cancelMessage])
      return true
    }

    return false
  }

  const { handleWSIRegenConfirmation: _handleWSIRegenConfirmation, handleSensitiveFieldsConfirmation: _handleSensitiveFieldsConfirmation } = useMessageConfirmationHandlers({
    user,
    resolvedCompanyId: null,
    isInJobCreationMode,
    setMessages,
    setIsLoading,
    awaitingWSIRegenerationConfirmation,
    setAwaitingWSIRegenerationConfirmation,
    wsiCandidates,
    setWsiCandidates,
    basicInfoFields,
    technicalSkills,
    behavioralCompetencies,
    awaitingSensitiveFieldsConfirmation,
    setAwaitingSensitiveFieldsConfirmation,
    fastTrackAppliedData,
    setFastTrackAppliedData,
    setBasicInfoFields,
    setJobConfig,
    setDetectedCriteria,
    setCurrentStage,
    setWizardMode,
    analytics,
  })

  const _handleFastTrackSuggestions = (content: string) => handleFastTrackSuggestions(content, ctx)
  const _handleFastTrackFlow = (content: string) => handleFastTrackFlow(content, ctx)
  const _handleCompensationMessage = (content: string) => handleCompensationMessage(content, ctx)
  const _handleLocalCommands = (content: string) => handleLocalCommands(content, ctx)

  return {
    _handleContextSwitch,
    _handleStageAdvanceConfirmation,
    _handleDraftChoice,
    _handleCalibrationChoice,
    _handlePendingToolConfirmation,
    _handleWSIRegenConfirmation,
    _handleSensitiveFieldsConfirmation,
    _handleFastTrackSuggestions,
    _handleFastTrackFlow,
    _handleCompensationMessage,
    _handleLocalCommands,
  }
}
