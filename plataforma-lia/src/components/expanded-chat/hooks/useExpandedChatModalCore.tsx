"use client"

import { useExpandedChatCoreState } from './useExpandedChatCoreState'
import { useExpandedChatCoreHooks } from './useExpandedChatCoreHooks'
import { useExpandedChatWiring } from './useExpandedChatWiring'
import { type ExpandedChatModalProps } from '../types'

export function useExpandedChatModalCore({
  isOpen,
  onClose,
  onMinimize,
  initialMessage,
  initialMessages,
  contextTitle = "Criação de Vaga",
  inline = false,
  mode = 'general',
  onJobCreated,
  onReturnToLateral,
  hideModeButtons = false,
  onOrchestratedMessage,
  onFullscreenChange,
  onMessagesUpdate
}: ExpandedChatModalProps) {
  const state = useExpandedChatCoreState(mode)

  const hooks = useExpandedChatCoreHooks({
    user: state.user,
    isJobCreationMode: state.isJobCreationMode,
    isOpen,
    mode,
    messages: state.messages,
    setMessages: state.setMessages,
    currentStage: state.currentStage,
    setCurrentStage: state.setCurrentStage,
    detectedCriteria: state.detectedCriteria,
    setDetectedCriteria: state.setDetectedCriteria,
    basicInfoFields: state.basicInfoFields,
    setBasicInfoFields: state.setBasicInfoFields,
    setFieldOrigins: state.setFieldOrigins,
    conversationId: state.conversationId,
    setConversationId: state.setConversationId,
    messagesEndRef: state.messagesEndRef,
    wizardMode: state.wizardMode,
    setWizardMode: state.setWizardMode,
    setTechnicalSkills: state.setTechnicalSkills,
    setBehavioralCompetencies: state.setBehavioralCompetencies,
    setSalaryInfo: state.setSalaryInfo,
    setWsiQuestions: state.setWsiQuestions,
    setGeneratedJobDescription: state.setGeneratedJobDescription,
    setWizardFastTrackSourceJobId: state.setWizardFastTrackSourceJobId,
    wizardDraftId: state.wizardDraftId,
    fastTrackMessageSent: state.fastTrackMessageSent,
    setFastTrackMessageSent: state.setFastTrackMessageSent,
    fastTrackSuggestionsShownTracked: state.fastTrackSuggestionsShownTracked,
    setFastTrackSuggestionsShownTracked: state.setFastTrackSuggestionsShownTracked,
    awaitingFastTrackSelection: state.awaitingFastTrackSelection,
    setAwaitingFastTrackSelection: state.setAwaitingFastTrackSelection,
    resetFastTrackConversationState: state.resetFastTrackConversationState,
  })

  return useExpandedChatWiring({
    state, hooks, isOpen, initialMessage, initialMessages, mode,
    onClose, onJobCreated, inline, onOrchestratedMessage, onMessagesUpdate,
  })
}
