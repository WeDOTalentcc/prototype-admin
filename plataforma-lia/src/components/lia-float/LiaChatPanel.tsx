/**
 * @deprecated Use UnifiedChat (sidebar mode) via InlineChatBridge instead.
 * This component is replaced by the unified chat architecture (Phase 6).
 * Migration: import { InlineChatBridge } from "@/components/unified-chat"
 */
"use client"

import React, { useMemo, useCallback } from "react"
import { ArrowRight } from "lucide-react"
import { useRouter } from "next/navigation"
import { cn } from "@/lib/utils"
import { FairnessWarningBanner } from "@/components/fairness-warning-banner"
import { useLiaChatPanelState } from "@/components/lia-float/useLiaChatPanelState"
import { LiaChatHeader } from "@/components/lia-float/LiaChatHeader"
import { LiaChatMessageList, pageToUrl } from "@/components/lia-float/LiaChatMessageList"
import { LiaChatInput } from "@/components/lia-float/LiaChatInput"
import { DynamicContextPanel } from "@/components/lia-float/panels"
import { ModeLabel } from "@/components/lia-float/ModeLabel"
import { SwitchTaskModal } from "@/components/lia-float/SwitchTaskModal"
import { BackgroundAgentsStatus, type BackgroundTask } from "@/components/lia-float/BackgroundAgentsStatus"
import { BackgroundTaskNotification } from "@/components/lia-float/BackgroundTaskNotification"

export function LiaChatPanel() {
  const state = useLiaChatPanelState()
  const router = useRouter()

  const bgTasks: BackgroundTask[] = useMemo(() =>
    (state.backgroundTasks ?? []).map(t => ({
      id: t.task_id,
      type: t.task_type,
      label: t.label,
      status: t.status,
      progress: t.progress,
      message: t.message,
      result: t.result,
    })),
    [state.backgroundTasks]
  )

  const completedTasks = useMemo(() =>
    bgTasks.filter(t => t.status === "completed" || t.status === "failed"),
    [bgTasks]
  )

  const handleSelectSession = useCallback((sessionId: string) => {
    state.handleLoadConversation(sessionId)
  }, [state])

  const handleClearMode = useCallback(() => {
    state.setActiveActionType(null)
    state.setActionLabel(null)
  }, [state])

  const handleDismissTask = useCallback((taskId: string) => {
    state.clearBackgroundTask(taskId)
  }, [state])

  const handleViewResult = useCallback((task: BackgroundTask) => {
    const resultSummary = task.message || "Tarefa concluída"
    state.addMessage({
      id: `bg-result-${task.id}-${Date.now()}`,
      sender: "lia" as const,
      content: `**${task.label}** — ${resultSummary}`,
      timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
    })
    state.clearBackgroundTask(task.id)
  }, [state])

  if (!state.isOpen) return null

  const hasDynamicPanel = !!state.dynamicPanel

  return (
    <>
      <div
        className={cn(
          "fixed bottom-[84px] left-6 z-50",
          hasDynamicPanel ? "w-[840px]" : "w-[420px]",
          "h-[580px]",
          "flex flex-row",
          "bg-lia-bg-primary",
          "border border-lia-border-subtle",
          "rounded-xl shadow-lia-lg overflow-hidden",
          "transition-[width] duration-300 ease-in-out"
        )}
        role="dialog"
        aria-label="Chat LIA"
      >
        <div className="w-[420px] min-w-[420px] flex flex-col h-full">
          <LiaChatHeader
            isConnected={state.isConnected}
            showHistory={state.showHistory}
            messagesLength={state.messages.length}
            activeActionType={state.activeActionType}
            actionLabel={state.actionLabel}
            isReconnecting={state.isReconnecting}
            reconnectAttempt={state.reconnectAttempt}
            contextPage={state.contextPage}
            entityContext={state.entityContext}
            handleNewChat={state.handleNewChat}
            handleClear={state.handleClear}
            handleToggleHistory={state.handleToggleHistory}
            handleExpand={state.handleExpand}
            close={state.close}
            setActiveActionType={state.setActiveActionType}
            setActionLabel={state.setActionLabel}
            onSwitchTask={() => state.setShowSwitchTask(true)}
          />

          <LiaChatMessageList
            showHistory={state.showHistory}
            recentChats={state.recentChats}
            handleLoadConversation={state.handleLoadConversation}
            isFetchingHistory={state.isFetchingHistory}
            isEmpty={state.isEmpty}
            messages={state.messages}
            currentScope={state.currentScope}
            contextPage={state.contextPage}
            handleChipSend={state.handleChipSend}
            hitlPending={state.hitlPending}
            sendApproval={state.sendApproval}
            isStreaming={state.isStreaming}
            streamingContent={state.streamingContent}
            conversationId={state.conversationId}
            messagesEndRef={state.messagesEndRef}
          />

          {completedTasks.length > 0 && (
            <div className="px-4 py-2 space-y-2 flex-shrink-0">
              {completedTasks.map(task => (
                <BackgroundTaskNotification
                  key={task.id}
                  task={task}
                  onViewResult={handleViewResult}
                  onDismiss={handleDismissTask}
                />
              ))}
            </div>
          )}

          <FairnessWarningBanner
            warnings={state.fairnessWarnings}
            onDismiss={state.dismissFairnessWarnings}
          />

          <BackgroundAgentsStatus
            tasks={bgTasks}
            onViewResult={handleViewResult}
          />

          {state.navIntent?.page && (
            <div className="px-4 py-2 border-t border-lia-border-subtle flex-shrink-0">
              <button
                onClick={() => {
                  if (state.navIntent?.page) {
                    const url = pageToUrl(state.navIntent.page)
                    state.close()
                    state.expand()
                    if (url) router.push(url)
                    state.clearIntent()
                  }
                }}
                className="flex items-center gap-2 text-sm-ui text-lia-text-tertiary hover:text-lia-text-primary dark:hover:text-lia-text-inverse transition-colors motion-reduce:transition-none group w-full text-left"
                aria-label={`Abrir ${state.navIntent.page}`}
              >
                <ArrowRight className="w-3.5 h-3.5 flex-shrink-0 text-wedo-cyan group-hover:translate-x-0.5 transition-transform motion-reduce:transition-none" />
                <span>{state.navIntent.hint ?? `Ver em ${state.navIntent.page}`}</span>
              </button>
            </div>
          )}

          <div className="flex-shrink-0">
            {state.activeActionType && state.actionLabel && (
              <div className="px-4 pt-2">
                <ModeLabel
                  actionType={state.activeActionType}
                  actionLabel={state.actionLabel}
                  onClear={handleClearMode}
                />
              </div>
            )}
            <LiaChatInput
              inputText={state.inputText}
              setInputText={state.setInputText}
              maxInputChars={state.MAX_INPUT_CHARS}
              attachedCvFile={state.attachedCvFile}
              setAttachedCvFile={state.setAttachedCvFile}
              cvFileInputRef={state.cvFileInputRef}
              inputRef={state.inputRef}
              handleCvFileAttach={state.handleCvFileAttach}
              handleCvFileButtonClick={state.handleCvFileButtonClick}
              handleSend={state.handleSend}
              handleKeyDown={state.handleKeyDown}
              isCreating={state.isCreating}
              isStreaming={state.isStreaming}
              isScreening={state.isScreening}
              hitlPending={state.hitlPending}
              canSend={state.canSend}
              contextPage={state.contextPage}
              contextDismissed={state.contextDismissed}
              onContextDismiss={() => state.setContextDismissed(true)}
            />
          </div>
        </div>

        {hasDynamicPanel && state.dynamicPanel && (
          <DynamicContextPanel
            panel={state.dynamicPanel}
            className="w-[420px] min-w-[420px]"
          />
        )}
      </div>

      <SwitchTaskModal
        isOpen={state.showSwitchTask}
        onClose={() => state.setShowSwitchTask(false)}
        onSelectSession={handleSelectSession}
        currentSessionId={state.conversationId}
      />
    </>
  )
}
