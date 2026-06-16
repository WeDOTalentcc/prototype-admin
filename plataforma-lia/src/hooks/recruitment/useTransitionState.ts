"use client"

import { useState, useMemo, useEffect, useCallback } from 'react'
import type {
  CandidateContext,
  JobContext,
  TransitionAction,
  SubStatusOption,
  UseTransitionContextOptions,
} from './transition-context-types'
import {
  TRANSITION_API_BASE as API_BASE,
  fetchWithTimeoutTransition as fetchWithTimeout,
  getAvailableActionsForTransition,
  getDefaultSubStatus,
  getDefaultSubStatusOptions,
} from './transition-context-types'

export interface UseTransitionStateReturn {
  availableActions: TransitionAction[]
  predictedSubStatuses: Record<string, string>
  setPredictedSubStatuses: React.Dispatch<React.SetStateAction<Record<string, string>>>
  predictionReasonings: Record<string, string>
  isPredicting: boolean
  subStatusOptions: SubStatusOption[]
  selectedAction: TransitionAction | null
  setSelectedAction: (action: TransitionAction | null) => void
  channel: 'email' | 'whatsapp'
  setChannel: (channel: 'email' | 'whatsapp') => void
}

/**
 * Manages the state side of a stage transition: available actions,
 * sub-status predictions, and channel/action selection.
 */
export function useTransitionState(options: UseTransitionContextOptions): UseTransitionStateReturn {
  const { candidates, fromStage, toStage, jobContext } = options

  const [predictedSubStatuses, setPredictedSubStatuses] = useState<Record<string, string>>({})
  const [predictionReasonings, setPredictionReasonings] = useState<Record<string, string>>({})
  const [isPredicting, setIsPredicting] = useState(false)
  const [subStatusOptions, setSubStatusOptions] = useState<SubStatusOption[]>([])
  const [selectedAction, setSelectedAction] = useState<TransitionAction | null>(null)
  const [channel, setChannel] = useState<'email' | 'whatsapp'>('email')

  const availableActions = useMemo(() => {
    return getAvailableActionsForTransition(fromStage, toStage)
  }, [fromStage, toStage])

  useEffect(() => {
    if (availableActions.length > 0) {
      const recommended = availableActions.find(a => a.recommended) || availableActions[0]
      setSelectedAction(recommended)
    }
  }, [availableActions])

  // Fetch sub-status options for target stage
  useEffect(() => {
    async function fetchSubStatusOptions() {
      try {
        const response = await fetchWithTimeout(
          `${API_BASE}/stage-automation/substatus-options/${toStage}`,
          { method: 'GET', headers: { 'Content-Type': 'application/json' } }
        )
        if (response.ok) {
          const data = await response.json()
          setSubStatusOptions(data.options || [])
        }
      } catch (err) {
        setSubStatusOptions(getDefaultSubStatusOptions(toStage))
      }
    }

    fetchSubStatusOptions()
  }, [toStage])

  // Predict sub-statuses for all candidates
  useEffect(() => {
    async function predictAllBulk() {
      if (candidates.length === 0) return

      setIsPredicting(true)
      const predictions: Record<string, string> = {}
      const reasonings: Record<string, string> = {}

      try {
        const response = await fetchWithTimeout(
          `${API_BASE}/stage-automation/bulk-predict-substatus`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              candidates: candidates.map(c => ({
                id: c.id,
                name: c.name,
                email: c.email,
                phone: c.phone,
                current_title: c.current_title,
                current_company: c.current_company,
                wsi_score: c.wsi_score,
                interview_notes: c.interview_notes || [],
                lia_parecer: c.lia_parecer
              })),
              from_stage: fromStage,
              to_stage: toStage,
              job_context: jobContext
            })
          }
        )

        if (response.ok) {
          const data = await response.json()
          if (data.predictions && Array.isArray(data.predictions)) {
            for (const pred of data.predictions) {
              predictions[pred.candidate_id] = pred.predicted_substatus
              if (pred.reasoning) {
                reasonings[pred.candidate_id] = pred.reasoning
              }
            }
          }
        }

        for (const candidate of candidates) {
          if (!predictions[candidate.id]) {
            predictions[candidate.id] = getDefaultSubStatus(toStage)
          }
        }

        setPredictedSubStatuses(predictions)
        setPredictionReasonings(reasonings)
      } catch (err) {
        for (const candidate of candidates) {
          predictions[candidate.id] = getDefaultSubStatus(toStage)
        }
        setPredictedSubStatuses(predictions)
      } finally {
        setIsPredicting(false)
      }
    }

    async function predictAllOneByOne() {
      if (candidates.length === 0) return

      setIsPredicting(true)
      const predictions: Record<string, string> = {}

      try {
        for (const candidate of candidates) {
          try {
            const response = await fetchWithTimeout(
              `${API_BASE}/stage-automation/predict-substatus`,
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
                  from_stage: fromStage,
                  to_stage: toStage,
                  job_context: jobContext
                })
              }
            )

            if (response.ok) {
              const data = await response.json()
              predictions[candidate.id] = data.predicted_substatus
            } else {
              predictions[candidate.id] = getDefaultSubStatus(toStage)
            }
          } catch (err) {
            predictions[candidate.id] = getDefaultSubStatus(toStage)
          }
        }

        setPredictedSubStatuses(predictions)
      } finally {
        setIsPredicting(false)
      }
    }

    if (candidates.length > 1 && toStage === 'rejected') {
      predictAllBulk()
    } else {
      predictAllOneByOne()
    }
  }, [candidates, fromStage, toStage, jobContext])

  return {
    availableActions,
    predictedSubStatuses,
    setPredictedSubStatuses,
    predictionReasonings,
    isPredicting,
    subStatusOptions,
    selectedAction,
    setSelectedAction,
    channel,
    setChannel,
  }
}
