"use client"

/**
 * LiaChatShell — Wrapper que renderiza o chat unificado em diferentes modos de apresentação.
 *
 * Modos suportados:
 *   - "inline-left"  → coluna esquerda fixa integrada ao layout da página
 *                      (Jobs list, Kanban/job view)
 *   - "full-page"    → tela cheia, usado na rota /chat
 *
 * Modo flutuante (padrão) é gerenciado pelo componente LiaFloatConditional existente,
 * não por este shell.
 *
 * Consome useLiaChatPanelState para compartilhar estado de conversa/WebSocket
 * entre todos os modos via lia-float-context.
 * Sugestões contextuais específicas da página via prop `contextChips`.
 */

import React, { useMemo, useCallback, useEffect } from "react"
import { ArrowRight } from "lucide-react"
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
import { useLiaFloat } from "@/contexts/lia-float-context"
import { useRouter } from "next/navigation"

export type LiaChatShellMode = "inline-left" | "full-page"

export interface ContextChip {
  id: string
  label: string
  prompt: string
  icon?: React.ReactNode
}

interface LiaChatShellProps {
  mode: LiaChatShellMode
  /** Chips de sugestão contextuais específicos da página */
  contextChips?: ContextChip[]
  /** Callback para fechar/colapsar quando está em modo inline */
  onClose?: () => void
  /** Largura do painel em modo inline-left (px ou string CSS) */
  width?: number | string
  /** Classe CSS adicional para o container */
  className?: string
}

/**
 * LiaChatShell in "inline-left" mode — painel lateral esquerdo integrado ao layout
 */
function InlineLeftShell({
  contextChips,
  onClose,
  width = 400,
  className,
}: Omit<LiaChatShellProps, "mode">) {
  const { open, setHasInlineChat } = useLiaFloat()
  const state = useLiaChatPanelState()
  const router = useRouter()

  useEffect(() => {
    open()
    setHasInlineChat(true)
    return () => { setHasInlineChat(false) }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

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

  const handleClose = useCallback(() => {
    if (onClose) {
      onClose()
    } else {
      state.close()
    }
  }, [onClose, state])

  const hasDynamicPanel = !!state.dynamicPanel

  const panelWidth = typeof width === "number" ? `${width}px` : width

  return (
    <>
      <div
        className={cn(
          "flex flex-col h-full",
          "bg-lia-bg-primary",
          "border border-lia-border-subtle",
          "rounded-md overflow-hidden",
          "transition-[width] duration-300 ease-in-out",
          className
        )}
        style={{ width: panelWidth, minWidth: panelWidth, maxWidth: hasDynamicPanel ? undefined : panelWidth }}
        role="complementary"
        aria-label="Chat LIA"
      >
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
          close={handleClose}
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
          {contextChips && contextChips.length > 0 && (
            <div className="px-4 pb-3 pt-1 flex items-center gap-1.5 flex-wrap">
              <span className="text-micro font-medium text-lia-text-tertiary">Sugestões:</span>
              {contextChips.map(chip => (
                <button
                  key={chip.id}
                  onClick={() => state.handleChipSend(chip.prompt)}
                  className="inline-flex items-center gap-1 px-2 py-0.5 text-micro font-medium text-lia-text-secondary bg-lia-bg-tertiary rounded-full hover:bg-lia-interactive-active transition-colors motion-reduce:transition-none"
                  aria-label={chip.label}
                >
                  {chip.icon}
                  {chip.label}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {hasDynamicPanel && state.dynamicPanel && (
        <DynamicContextPanel
          panel={state.dynamicPanel}
          className="w-[420px] min-w-[420px] border border-lia-border-subtle rounded-md ml-2"
        />
      )}

      <SwitchTaskModal
        isOpen={state.showSwitchTask}
        onClose={() => state.setShowSwitchTask(false)}
        onSelectSession={handleSelectSession}
        currentSessionId={state.conversationId}
      />
    </>
  )
}

/**
 * LiaChatShell in "full-page" mode — ocupa toda a área disponível
 */
function FullPageShell({ className }: Pick<LiaChatShellProps, "className">) {
  const { open, setHasInlineChat } = useLiaFloat()
  const state = useLiaChatPanelState()
  const router = useRouter()

  useEffect(() => {
    open()
    setHasInlineChat(true)
    return () => { setHasInlineChat(false) }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

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

  const hasDynamicPanel = !!state.dynamicPanel

  return (
    <>
      <div
        className={cn(
          "flex flex-row h-full w-full",
          "bg-lia-bg-primary",
          "border border-lia-border-subtle",
          "rounded-md overflow-hidden",
          className
        )}
        role="main"
        aria-label="Chat LIA — tela cheia"
      >
        <div className={cn("flex flex-col h-full", hasDynamicPanel ? "flex-1" : "w-full")}>
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
                className="flex items-center gap-2 text-sm-ui text-lia-text-tertiary hover:text-lia-text-primary transition-colors motion-reduce:transition-none group w-full text-left"
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
            className="w-[420px] min-w-[420px] border-l border-lia-border-subtle"
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

/**
 * LiaChatShell — Entry point.
 * Seleciona o sub-componente correto com base no `mode`.
 */
export function LiaChatShell({ mode, contextChips, onClose, width, className }: LiaChatShellProps) {
  if (mode === "inline-left") {
    return (
      <InlineLeftShell
        contextChips={contextChips}
        onClose={onClose}
        width={width}
        className={className}
      />
    )
  }
  return <FullPageShell className={className} />
}
