"use client"

import React from "react"
import {
  type WizardStage,
  type ExtendedWizardStageConfig,
  WIZARD_STAGES,
  getMissingCriticalFields,
} from '..'
import { type Message } from '../types'
import { type DetectedCriteria } from '..'

interface UseProceedToNextStageParams {
  currentStageIndex: number
  detectedCriteria: DetectedCriteria
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>
  typeText: (text: string, messageId: string) => void
  setCurrentStage: React.Dispatch<React.SetStateAction<WizardStage>>
  saveWizardDraft: () => void
  setDisplayedText: React.Dispatch<React.SetStateAction<string>>
}

export function useProceedToNextStage({
  currentStageIndex,
  detectedCriteria,
  setMessages,
  typeText,
  setCurrentStage,
  saveWizardDraft,
  setDisplayedText,
}: UseProceedToNextStageParams) {
  const proceedToNextStage = () => {
    const nextIndex = currentStageIndex + 1
    if (nextIndex < WIZARD_STAGES.length) {
      const currentStageConfig = WIZARD_STAGES[currentStageIndex] as ExtendedWizardStageConfig
      const nextStage = WIZARD_STAGES[nextIndex] as ExtendedWizardStageConfig

      // Generate transition message from current stage
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

      // Check for missing recommended fields and add gentle reminders
      const missingFields = getMissingCriticalFields(currentStageConfig.id, detectedCriteria as unknown as Record<string, unknown>)
      if (missingFields.recommended.length > 0) {
        transitionContent += `\n\n📝 *Campos opcionais não preenchidos: ${missingFields.recommended.join(', ')}*`
      }

      // Add transition message first
      if (transitionContent) {
        const transitionMessage: Message = {
          id: `transition-${currentStageConfig.id}-${Date.now()}`,
          role: 'assistant',
          content: transitionContent,
          timestamp: new Date(),
          isTyping: true
        }
        setMessages(prev => [...prev, transitionMessage])

        // Type transition message, then after delay add next stage message
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
        }, 2000) // Wait 2 seconds for transition message to be read
      } else {
        // No transition config, proceed directly
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
  }

  return { proceedToNextStage }
}
