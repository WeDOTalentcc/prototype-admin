/**
 * @deprecated Use UnifiedChat (sidebar mode) via InlineChatBridge instead.
 * This component is replaced by the unified chat architecture (Phase 6).
 * Migration: import { InlineChatBridge } from "@/components/unified-chat"
 */
"use client"

import React from "react"
import dynamic from "next/dynamic"
import { useTranslations } from "next-intl"
import { LoadingModal } from "@/components/ui/loading"
import { Button } from "@/components/ui/button"
import { ChevronRight, Brain, Users } from "lucide-react"
import type { KanbanPageCoreState } from "@/components/pages/job-kanban/hooks/useKanbanPageCore"

const ExpandedChatModal = dynamic(() => import("@/components/expanded-chat-modal").then(m => ({ default: m.ExpandedChatModal })), { ssr: false, loading: () => <LoadingModal /> })

interface KanbanSuperChatSectionProps {
  state: KanbanPageCoreState
}

export function KanbanSuperChatSection({ state }: KanbanSuperChatSectionProps) {
  const t = useTranslations('kanban')
  const {
    liaPromptValue, liaMessages, candidatesData,
    setShowSuperChat, setUserCollapsedLIA,
    returnToExpandedPrompt, handleOrchestratedMessage,
  } = state

  return (
    <>
      <div
        className="flex-1 transition-colors motion-reduce:transition-none duration-300 pl-4 py-4 pr-0 min-w-0"
        style={{ maxWidth: 'calc(100% - 48px)' }}
      >
        <div className="h-full flex flex-col">
          <ExpandedChatModal
            isOpen={true}
            onClose={() => {
              setShowSuperChat(false)
              setUserCollapsedLIA(true)
            }}
            initialMessage={liaPromptValue}
            initialMessages={liaMessages.map(msg => ({
              id: msg.id,
              role: msg.type === 'user' ? 'user' : 'assistant',
              content: msg.content,
              timestamp: new Date(msg.timestamp)
            }))}
            contextTitle={t('candidateAnalysis')}
            inline={true}
            mode="general"
            onReturnToLateral={returnToExpandedPrompt}
            hideModeButtons={true}
            onOrchestratedMessage={handleOrchestratedMessage}
          />
        </div>
      </div>

      <div className="flex-shrink-0 w-12 transition-colors motion-reduce:transition-none duration-300 py-4 pr-2">
        <div className="h-[calc(100vh-12rem)] flex flex-col items-center bg-lia-bg-primary border border-lia-border-subtle rounded-xl py-3 gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowSuperChat(false)}
            className="h-8 w-8 p-0 rounded-md hover:bg-lia-bg-tertiary"
            title={t('expandView')}
          >
            <ChevronRight className="w-4 h-4 text-lia-text-tertiary" />
          </Button>

          <div className="w-6 h-px bg-lia-interactive-active my-1" />

          <div className="flex flex-col items-center gap-1 py-2 cursor-pointer hover:bg-lia-bg-secondary rounded-md px-2 transition-colors motion-reduce:transition-none">
            <div className="w-6 h-6 rounded-full bg-wedo-orange flex items-center justify-center">
              <span className="text-white text-micro font-bold">H</span>
            </div>
          </div>

          <div className="flex flex-col items-center gap-1 py-2 cursor-pointer hover:bg-lia-bg-secondary rounded-md px-2 transition-colors motion-reduce:transition-none">
            <div className="w-6 h-6 rounded-full bg-status-warning flex items-center justify-center">
              <Brain className="w-3.5 h-3.5 text-white" />
            </div>
          </div>

          <div className="flex-1" />

          <div
            className="flex flex-col items-center gap-1 py-3 cursor-pointer hover:bg-lia-bg-secondary rounded-md px-1 transition-colors motion-reduce:transition-none border-r-2 border-lia-btn-primary-bg dark:border-lia-border-medium"
            onClick={() => setShowSuperChat(false)}
          >
            <Users className="w-4 h-4 text-lia-text-secondary" />
            <span
              className="text-micro font-medium text-lia-text-secondary tracking-wide"
              style={{ writingMode: 'vertical-rl', textOrientation: 'mixed' }}
              aria-live="polite" aria-atomic="true">
              {t('candidatesCount', { count: Object.values(candidatesData).flat().length })}
            </span>
          </div>
        </div>
      </div>
    </>
  )
}
