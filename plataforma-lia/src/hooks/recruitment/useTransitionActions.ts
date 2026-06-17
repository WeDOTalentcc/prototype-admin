"use client"

import { useState, useCallback } from 'react'
import type {
  CandidateContext,
  JobContext,
  TransitionAction,
  GeneratedMessage,
} from './transition-context-types'
import {
  TRANSITION_API_BASE as API_BASE,
  fetchWithTimeoutTransition as fetchWithTimeout,
  getDefaultSubStatus,
  generateFallbackMessage,
  getSubStatusFromMessage,
} from './transition-context-types'

export interface UseTransitionActionsOptions {
  candidates: CandidateContext[]
  toStage: string
  jobContext: JobContext
  predictedSubStatuses: Record<string, string>
  selectedAction: TransitionAction | null
  channel: 'email' | 'whatsapp'
  setPredictedSubStatuses: React.Dispatch<React.SetStateAction<Record<string, string>>>
}

export interface UseTransitionActionsReturn {
  messages: Record<string, GeneratedMessage>
  generateMessages: (personalized: boolean) => Promise<void>
  regenerateMessage: (candidateId: string) => Promise<void>
  updateMessage: (candidateId: string, body: string, subject?: string) => void
  updateSubStatus: (candidateId: string, subStatus: string) => void
  isGenerating: boolean
  error: string | null
}

/**
 * Manages message generation, regeneration, and editing for stage transitions.
 */
export function useTransitionActions(options: UseTransitionActionsOptions): UseTransitionActionsReturn {
  const {
    candidates,
    toStage,
    jobContext,
    predictedSubStatuses,
    selectedAction,
    channel,
    setPredictedSubStatuses,
  } = options

  const [messages, setMessages] = useState<Record<string, GeneratedMessage>>({})
  const [isGenerating, setIsGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const generateMessages = useCallback(async (personalized: boolean) => {
    if (candidates.length === 0 || !selectedAction) return

    setIsGenerating(true)
    setError(null)
    const generated: Record<string, GeneratedMessage> = {}

    try {
      for (const candidate of candidates) {
        const subStatus = predictedSubStatuses[candidate.id] || getDefaultSubStatus(toStage)

        try {
          if (personalized) {
            const response = await fetchWithTimeout(
              `${API_BASE}/stage-automation/generate-message`,
              {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                  candidate_context: {
                    id: candidate.id,
                    name: candidate.name,
                    email: candidate.email,
                    phone: candidate.phone,
                    current_title: candidate.current_title,
                    current_company: candidate.current_company,
                    wsi_score: candidate.wsi_score,
                    interview_notes: candidate.interview_notes || [],
                    lia_parecer: candidate.lia_parecer
                  },
                  job_context: jobContext,
                  to_stage: toStage,
                  substatus: subStatus,
                  message_type: selectedAction.template_category || 'feedback_construtivo',
                  channel: channel
                })
              },
              45000
            )

            if (response.ok) {
              const data = await response.json()
              generated[candidate.id] = {
                subject: data.subject,
                body: data.body,
                isEdited: false,
                originalBody: data.body,
                ai_personalized: data.ai_personalized ?? false,
                predicted_sub_status: data.predicted_sub_status ?? subStatus
              }
            } else {
              generated[candidate.id] = generateFallbackMessage(candidate, toStage, subStatus, jobContext, channel)
            }
          } else {
            generated[candidate.id] = generateFallbackMessage(candidate, toStage, subStatus, jobContext, channel)
          }
        } catch (err) {
          generated[candidate.id] = generateFallbackMessage(candidate, toStage, subStatus, jobContext, channel)
        }
      }

      setMessages(generated)
    } catch (err) {
      setError('Erro ao gerar mensagens')
    } finally {
      setIsGenerating(false)
    }
  }, [candidates, predictedSubStatuses, toStage, jobContext, selectedAction, channel])

  const regenerateMessage = useCallback(async (candidateId: string) => {
    const candidate = candidates.find(c => c.id === candidateId)
    if (!candidate || !selectedAction) return

    const currentMessage = messages[candidateId]
    const oldSubStatus = currentMessage ? getSubStatusFromMessage(currentMessage.originalBody) : ''
    const newSubStatus = predictedSubStatuses[candidateId] || getDefaultSubStatus(toStage)

    setIsGenerating(true)

    try {
      if (currentMessage && oldSubStatus !== newSubStatus) {
        const response = await fetchWithTimeout(
          `${API_BASE}/stage-automation/regenerate-for-substatus`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              original_message: currentMessage.originalBody,
              old_substatus: oldSubStatus || 'profile_not_aligned',
              new_substatus: newSubStatus,
              candidate_context: {
                id: candidate.id,
                name: candidate.name,
                email: candidate.email,
                phone: candidate.phone,
                current_title: candidate.current_title,
                wsi_score: candidate.wsi_score,
                interview_notes: candidate.interview_notes || [],
                lia_parecer: candidate.lia_parecer
              },
              job_context: jobContext,
              channel: channel
            })
          },
          45000
        )

        if (response.ok) {
          const data = await response.json()
          setMessages(prev => ({
            ...prev,
            [candidateId]: {
              subject: data.subject || prev[candidateId]?.subject,
              body: data.body,
              isEdited: false,
              originalBody: data.body
            }
          }))
          return
        }
      }

      const response = await fetchWithTimeout(
        `${API_BASE}/stage-automation/generate-message`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            candidate_context: {
              id: candidate.id,
              name: candidate.name,
              email: candidate.email,
              phone: candidate.phone,
              current_title: candidate.current_title,
              wsi_score: candidate.wsi_score,
              interview_notes: candidate.interview_notes || [],
              lia_parecer: candidate.lia_parecer
            },
            job_context: jobContext,
            to_stage: toStage,
            substatus: newSubStatus,
            message_type: selectedAction.template_category || 'feedback_construtivo',
            channel: channel
          })
        },
        45000
      )

      if (response.ok) {
        const data = await response.json()
        setMessages(prev => ({
          ...prev,
          [candidateId]: {
            subject: data.subject,
            body: data.body,
            isEdited: false,
            originalBody: data.body
          }
        }))
      }
    } catch (err) {
      // silently fail like original
    } finally {
      setIsGenerating(false)
    }
  }, [candidates, messages, predictedSubStatuses, toStage, jobContext, selectedAction, channel])

  const updateSubStatus = useCallback((candidateId: string, subStatus: string) => {
    setPredictedSubStatuses(prev => ({
      ...prev,
      [candidateId]: subStatus
    }))

    regenerateMessage(candidateId)
  }, [regenerateMessage, setPredictedSubStatuses])

  const updateMessage = useCallback((candidateId: string, body: string, subject?: string) => {
    setMessages(prev => ({
      ...prev,
      [candidateId]: {
        ...prev[candidateId],
        body,
        subject: subject !== undefined ? subject : prev[candidateId]?.subject,
        isEdited: body !== prev[candidateId]?.originalBody
      }
    }))
  }, [])

  return {
    messages,
    generateMessages,
    regenerateMessage,
    updateMessage,
    updateSubStatus,
    isGenerating,
    error,
  }
}
