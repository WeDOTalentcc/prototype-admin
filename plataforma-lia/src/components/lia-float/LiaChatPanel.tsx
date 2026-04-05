"use client"

import React from "react"
import { ArrowRight } from "lucide-react"
import { useRouter } from "next/navigation"
import { cn } from "@/lib/utils"
import { FairnessWarningBanner } from "@/components/fairness-warning-banner"
import { useLiaChatPanelState } from "@/components/lia-float/useLiaChatPanelState"
import { LiaChatHeader } from "@/components/lia-float/LiaChatHeader"
import { LiaChatMessageList, pageToUrl } from "@/components/lia-float/LiaChatMessageList"
import { LiaChatInput } from "@/components/lia-float/LiaChatInput"

export function LiaChatPanel() {
  const state = useLiaChatPanelState()
  const router = useRouter()

  if (!state.isOpen) return null

  return (
    <div
      className={cn(
        "fixed bottom-[84px] right-6 z-50",
        "w-[420px] h-[580px]",
        "flex flex-col",
        "bg-lia-bg-primary",
        "border border-lia-border-subtle",
        "rounded-xl shadow-lia-lg overflow-hidden"
      )}
      role="dialog"
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
        handleNewChat={state.handleNewChat}
        handleClear={state.handleClear}
        handleToggleHistory={state.handleToggleHistory}
        handleExpand={state.handleExpand}
        close={state.close}
        setActiveActionType={state.setActiveActionType}
        setActionLabel={state.setActionLabel}
      />

      <LiaChatMessageList
        showHistory={state.showHistory}
        recentChats={state.recentChats}
        handleLoadConversation={state.handleLoadConversation}
        isFetchingHistory={state.isFetchingHistory}
        isEmpty={state.isEmpty}
        messages={state.messages}
        currentScope={state.currentScope}
        handleChipSend={state.handleChipSend}
        hitlPending={state.hitlPending}
        sendApproval={state.sendApproval}
        isStreaming={state.isStreaming}
        streamingContent={state.streamingContent}
        conversationId={state.conversationId}
        messagesEndRef={state.messagesEndRef}
      />

      <FairnessWarningBanner
        warnings={state.fairnessWarnings}
        onDismiss={state.dismissFairnessWarnings}
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
      />
    </div>
  )
}
