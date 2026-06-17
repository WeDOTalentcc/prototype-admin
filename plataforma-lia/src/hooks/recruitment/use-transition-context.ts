"use client"

/**
 * useTransitionContext — Facade hook.
 *
 * Composes useTransitionState and useTransitionActions into the original
 * combined interface so existing consumers need zero changes.
 */

// Re-export all public types
export type {
  WSIScore,
  InterviewNote,
  LiaParecer,
  CandidateContext,
  JobContext,
  TransitionAction,
  GeneratedMessage,
  SubStatusOption,
} from './transition-context-types'

// Re-export sub-hooks for direct use
export { useTransitionState } from './useTransitionState'
export { useTransitionActions } from './useTransitionActions'

import type { UseTransitionContextOptions, UseTransitionContextReturn } from './transition-context-types'
import { useTransitionState } from './useTransitionState'
import { useTransitionActions } from './useTransitionActions'

export function useTransitionContext(options: UseTransitionContextOptions): UseTransitionContextReturn {
  const {
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
  } = useTransitionState(options)

  const {
    messages,
    generateMessages,
    regenerateMessage,
    updateMessage,
    updateSubStatus,
    isGenerating,
    error,
  } = useTransitionActions({
    candidates: options.candidates,
    toStage: options.toStage,
    jobContext: options.jobContext,
    predictedSubStatuses,
    selectedAction,
    channel,
    setPredictedSubStatuses,
  })

  return {
    availableActions,
    predictedSubStatuses,
    predictionReasonings,
    updateSubStatus,
    messages,
    generateMessages,
    regenerateMessage,
    updateMessage,
    isGenerating,
    isPredicting,
    error,
    subStatusOptions,
    selectedAction,
    setSelectedAction,
    channel,
    setChannel,
  }
}
