"use client"

import { useCallback, useMemo } from "react"
import { type GroupedChange } from '.'
import type { Message } from '../types'
import {
  type DetectedCriteria,
  type WizardStage,
  WIZARD_STAGES,
  getMissingCriticalFields,
  type ExtendedWizardStageConfig,
} from '..'
import { extractCriteriaFromText as _extractCriteria } from "./expandedChatCriteriaExtractor"

export interface ProactiveHandlerDeps {
  user: Record<string, unknown> | null | undefined
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>
}

export interface GroupedPanelChangeDeps {
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>
}

export interface ProceedToNextStageDeps {
  currentStageIndex: number
  detectedCriteria: DetectedCriteria
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>
  setCurrentStage: (stage: WizardStage) => void
  setDisplayedText: (text: string) => void
  typeText: (text: string, id: string) => void
  saveWizardDraft: () => void
}

export interface ExtractCriteriaDeps {
  detectedCriteria: DetectedCriteria
  setDetectedCriteria: React.Dispatch<React.SetStateAction<DetectedCriteria>>
}

export function useProactiveHandlers({ user, setMessages }: ProactiveHandlerDeps) {
  const handleProactiveAccept = useCallback(async (actionId: string, messageId: string) => {
    const userId = (user as Record<string, unknown>)?.id as string || 'default_user'
    try {
      const res = await fetch(`/api/backend-proxy/proactive-actions?path=accept/${actionId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId }),
      })
      if (res.ok) {
        setMessages(prev => prev.filter(m => m.id !== messageId))
        const confirmMsg: Message = {
          id: `proactive-confirm-${Date.now()}`,
          role: 'assistant',
          content: '✅ Ação aceita! Estou processando...',
          timestamp: new Date(),
        }
        setMessages(prev => [...prev, confirmMsg])
      }
    } catch {
      // Silently ignore
    }
  }, [user, setMessages])

  const handleProactiveReject = useCallback(async (actionId: string, messageId: string) => {
    const userId = (user as Record<string, unknown>)?.id as string || 'default_user'
    try {
      const res = await fetch(`/api/backend-proxy/proactive-actions?path=reject/${actionId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId }),
      })
      if (res.ok) {
        setMessages(prev => prev.filter(m => m.id !== messageId))
      }
    } catch {
      // Silently ignore
    }
  }, [user, setMessages])

  return { handleProactiveAccept, handleProactiveReject }
}

export function useGroupedPanelChangeHandler({ setMessages }: GroupedPanelChangeDeps) {
  const handleGroupedPanelChange = useCallback((group: GroupedChange) => {
    if (group.changes.length === 0) return

    const panelChanges = group.changes.filter(c => c.source === 'panel')
    if (panelChanges.length === 0) return

    const systemMessage: Message = {
      id: `panel-sync-${Date.now()}`,
      role: 'assistant',
      content: `📝 ${group.summary}`,
      timestamp: new Date(),
      messageType: 'text',
      isFieldUpdate: true
    }
    setMessages(prev => [...prev, systemMessage])
  }, [setMessages])

  return { handleGroupedPanelChange }
}

export function useProceedToNextStage({
  currentStageIndex,
  detectedCriteria,
  setMessages,
  setCurrentStage,
  setDisplayedText,
  typeText,
  saveWizardDraft,
}: ProceedToNextStageDeps) {
  const proceedToNextStage = useCallback(() => {
    const nextIndex = currentStageIndex + 1
    if (nextIndex < WIZARD_STAGES.length) {
      const currentStageConfig = WIZARD_STAGES[currentStageIndex] as ExtendedWizardStageConfig
      const nextStage = WIZARD_STAGES[nextIndex] as ExtendedWizardStageConfig

      let transitionContent = ""
      if (currentStageConfig.transition) {
        const { congratsMessage, nextStepExplanation, whyItMatters, proactiveTips } = currentStageConfig.transition
        transitionContent = `${congratsMessage}\n\n`
        transitionContent += `**Próximo passo:** ${nextStepExplanation}\n\n`
        transitionContent += `💡 *${whyItMatters}*`

        if (proactiveTips && proactiveTips.length > 0) {
          transitionContent += `\n\n**O que vou fazer:**\n`
          proactiveTips.forEach(tip => {
            transitionContent += `• ${tip}\n`
          })
        }
      }

      const missingFields = getMissingCriticalFields(currentStageConfig.id, detectedCriteria as unknown as Record<string, unknown>)
      if (missingFields.recommended.length > 0) {
        transitionContent += `\n\n📝 *Campos opcionais não preenchidos: ${missingFields.recommended.join(', ')}*`
      }

      if (transitionContent) {
        const transitionMessage: Message = {
          id: `transition-${currentStageConfig.id}-${Date.now()}`,
          role: 'assistant',
          content: transitionContent,
          timestamp: new Date(),
          isTyping: true
        }
        setMessages(prev => [...prev, transitionMessage])

        typeText(transitionContent, transitionMessage.id)

        setTimeout(() => {
          setCurrentStage(nextStage.id)
          saveWizardDraft()

          const stageMessage: Message = {
            id: `stage-${nextStage.id}-${Date.now()}`,
            role: 'assistant',
            content: nextStage.liaMessage,
            timestamp: new Date(),
            isTyping: true
          }

          setMessages(prev => [...prev, stageMessage])
          setDisplayedText("")
          setTimeout(() => {
            typeText(nextStage.liaMessage, stageMessage.id)
          }, 300)
        }, 2000)
      } else {
        setCurrentStage(nextStage.id)
        saveWizardDraft()

        const stageMessage: Message = {
          id: `stage-${nextStage.id}-${Date.now()}`,
          role: 'assistant',
          content: nextStage.liaMessage,
          timestamp: new Date(),
          isTyping: true
        }

        setMessages(prev => [...prev, stageMessage])
        setDisplayedText("")
        setTimeout(() => {
          typeText(nextStage.liaMessage, stageMessage.id)
        }, 300)
      }
    }
  }, [currentStageIndex, detectedCriteria, setMessages, setCurrentStage, setDisplayedText, typeText, saveWizardDraft])

  return { proceedToNextStage }
}

export function useExtractCriteria({ detectedCriteria, setDetectedCriteria }: ExtractCriteriaDeps) {
  const extractCriteriaFromText = useCallback((text: string) => {
    const result = _extractCriteria(text, detectedCriteria)
    setDetectedCriteria(result)
    return result
  }, [detectedCriteria, setDetectedCriteria])

  return { extractCriteriaFromText }
}

export function useCheckForExistingDraftSync({
  STAGE_DISPLAY_NAMES,
  INITIAL_STAGES,
}: {
  STAGE_DISPLAY_NAMES: Record<string, string>
  INITIAL_STAGES: string[]
}) {
  const checkForExistingDraftSync = useCallback((): {
    hasDraft: boolean
    stageName: string | null
    draftData: Record<string, unknown> | null
  } => {
    if (typeof window === 'undefined') return { hasDraft: false, stageName: null, draftData: null }
    try {
      const storedDraft = localStorage.getItem('wizard_draft')
      if (!storedDraft) return { hasDraft: false, stageName: null, draftData: null }

      const parsedDraft = JSON.parse(storedDraft) as Record<string, unknown>
      const currentStage = parsedDraft?.currentStage as string | undefined

      const hasMeaningfulDraft = currentStage && !INITIAL_STAGES.includes(currentStage)

      if (hasMeaningfulDraft) {
        return {
          hasDraft: true,
          stageName: STAGE_DISPLAY_NAMES[currentStage] || currentStage,
          draftData: parsedDraft
        }
      }
      return { hasDraft: false, stageName: null, draftData: null }
    } catch {
      return { hasDraft: false, stageName: null, draftData: null }
    }
  }, [STAGE_DISPLAY_NAMES, INITIAL_STAGES])

  return { checkForExistingDraftSync }
}
