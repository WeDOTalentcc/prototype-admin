/**
 * @deprecated Use UnifiedChat (sidebar mode) via InlineChatBridge instead.
 * This component is replaced by the unified chat architecture (Phase 6).
 * Migration: import { InlineChatBridge } from "@/components/unified-chat"
 */
"use client"

import React from "react"
import dynamic from "next/dynamic"
import { Briefcase, Plus, Star } from "lucide-react"
import { LiaChatShell } from "@/components/lia-float/LiaChatShell"
import { DynamicContextPanel } from "@/components/lia-float/panels"
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

const JOB_CHIPS = [
  { id: "criar-vaga", label: "Nova Vaga", prompt: "Criar uma nova vaga", icon: <Plus className="w-2.5 h-2.5" /> },
  { id: "analisar", label: "Analisar Funil", prompt: "Analisar o funil de todas as vagas", icon: <Briefcase className="w-2.5 h-2.5" /> },
  { id: "top-vagas", label: "Top Vagas", prompt: "Quais vagas têm melhor desempenho?", icon: <Star className="w-2.5 h-2.5" /> },
]

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
  const { dynamicPanel } = useLiaFloat()

  if (!showInlineChat && !showExpandedLIA) return null

  if (chatMode === "job-creation") {
    return (
      <div className="flex h-full">
        <div
          className={`transition-colors motion-reduce:transition-none duration-300 relative group h-full ${
            isTableCollapsed || isChatFullscreen ? "flex-1" : "flex-shrink-0"
          }`}
          style={{width:
              isTableCollapsed || isChatFullscreen
                ? "auto"
                : "60%",
            maxWidth:
              isTableCollapsed || isChatFullscreen
                ? "none"
                : "900px",
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

        {dynamicPanel && (
          <div className="w-[340px] flex-shrink-0 border-l border-lia-border-subtle animate-in slide-in-from-right-5 duration-300 h-full">
            <DynamicContextPanel panel={dynamicPanel} />
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="flex h-full flex-shrink-0" style={{ width: `${liaWidth}px` }}>
      <LiaChatShell
        mode="inline-left"
        contextChips={JOB_CHIPS}
        onClose={onCloseChat}
        width={liaWidth}
        className="h-full"
      />
    </div>
  )
}
