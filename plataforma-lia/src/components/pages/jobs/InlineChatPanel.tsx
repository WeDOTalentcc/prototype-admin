"use client"

import React, { useState, useRef, useEffect } from "react"
import dynamic from "next/dynamic"
import { useLiaFloat } from "@/contexts/lia-float-context"

const ExpandedChatModal = dynamic(
  () => import("@/components/expanded-chat-modal").then((m) => ({ default: m.ExpandedChatModal })),
  { ssr: false },
)

interface LiaInlineMessage {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: Date
  isTyping?: boolean
}

interface InlineChatPanelProps {
  showExpandedLIA: boolean
  showInlineChat: boolean
  chatMode: "general" | "job-creation" | null
  inlineChatInitialMessage?: string
  liaInlineMessages: LiaInlineMessage[]
  liaInlineLoading: boolean
  isChatFullscreen: boolean
  liaWidth: number
  isTableCollapsed: boolean
  isResizingLIA: boolean
  userCollapsedLIA: boolean
  selectedJobsForBatch: Set<number>

  liaPromptValue: string
  onSetLiaPromptValue: (value: string | ((prev: string) => string)) => void

  onCloseChat: () => void
  onOpenGeneralChat: (message?: string) => void
  onOpenJobCreationChat: (message?: string) => void
  onReturnToGeneralChat: () => void
  onReturnToLateralPrompt: (messages?: Array<{ id: string; role: "user" | "assistant"; content: string; timestamp: Date }>) => void
  onSendMessage: (content: string) => Promise<void>
  onSetShowExpandedLIA: (show: boolean) => void
  onSetUserCollapsedLIA: (collapsed: boolean) => void
  onSetIsChatFullscreen: (fullscreen: boolean) => void
  onSetIsResizingLIA: (resizing: boolean) => void
  onSetLiaWidth: (width: number) => void
  onSetLiaInlineMessages: (msgs: LiaInlineMessage[]) => void

  liaInlineMessagesEndRef: React.RefObject<HTMLDivElement>

  onAddRecentItem?: (item: {
    id: string
    type: "vaga" | "chat" | "candidato"
    title: string
    subtitle?: string
    meta?: Record<string, string | undefined>
  }) => void
}

export function InlineChatPanel({
  showExpandedLIA,
  showInlineChat,
  chatMode,
  inlineChatInitialMessage,
  liaInlineMessages,
  liaInlineLoading,
  isChatFullscreen,
  liaWidth,
  isTableCollapsed,
  isResizingLIA,
  userCollapsedLIA,
  selectedJobsForBatch,
  liaPromptValue,
  onSetLiaPromptValue,
  onCloseChat,
  onOpenGeneralChat,
  onOpenJobCreationChat,
  onReturnToGeneralChat,
  onReturnToLateralPrompt,
  onSendMessage,
  onSetShowExpandedLIA,
  onSetUserCollapsedLIA,
  onSetIsChatFullscreen,
  onSetIsResizingLIA,
  onSetLiaWidth,
  onSetLiaInlineMessages,
  liaInlineMessagesEndRef,
  onAddRecentItem,
}: InlineChatPanelProps) {
  const { open: openFloat } = useLiaFloat()

  useEffect(() => {
    if ((showExpandedLIA || (showInlineChat && chatMode === "general")) && chatMode !== "job-creation") {
      openFloat()
      onCloseChat()
      onSetShowExpandedLIA(false)
    }
  }, [showExpandedLIA, showInlineChat, chatMode]) // eslint-disable-line react-hooks/exhaustive-deps

  if (!showInlineChat || chatMode !== "job-creation") return null

  return (
    <div
      className={`transition-colors motion-reduce:transition-none duration-300 relative group h-full ${
        isTableCollapsed || (chatMode === "job-creation" && isChatFullscreen) ? "flex-1" : "flex-shrink-0"
      }`}
      style={{width:
          isTableCollapsed || (chatMode === "job-creation" && isChatFullscreen)
            ? "auto"
            : chatMode === "job-creation"
              ? "60%"
              : `${liaWidth}px`,
        maxWidth:
          isTableCollapsed || (chatMode === "job-creation" && isChatFullscreen)
            ? "none"
            : chatMode === "job-creation"
              ? "900px"
              : `${liaWidth}px`,
        transition: "all 0.3s ease-in-out"}}
    >
      <div className="h-full flex flex-col">
        <ExpandedChatModal
          isOpen={true}
          onClose={onCloseChat}
          initialMessage={inlineChatInitialMessage}
          initialMessages={liaInlineMessages}
          contextTitle="Criação de Vaga"
          inline={true}
          mode="job-creation"
          onJobCreated={() => {
            onReturnToGeneralChat()
          }}
          onReturnToLateral={onReturnToLateralPrompt}
          onFullscreenChange={onSetIsChatFullscreen}
          onMessagesUpdate={(msgs) => onSetLiaInlineMessages(msgs)}
        />
      </div>
    </div>
  )
}

