"use client"

import React, { useMemo } from "react"
import { Briefcase, Users, X, MessageSquare, ChevronRight, HelpCircle } from "lucide-react"
import { cn } from "@/lib/utils"
import { useTranslations } from 'next-intl'
import { useLiaFloat } from "@/contexts/lia-float-context"
import { useRecentItemsStore } from "@/stores/recent-items-store"
import type { ChatMode } from "./unified-chat-types"

interface Props {
  isOpen: boolean
  onClose: () => void
  mode: ChatMode
}

export function ContextConfigPanel({ isOpen, onClose, mode }: Props) {
  const t = useTranslations('chat.contextPanel')
  const { chatContextType, switchChatContext, entityContext, setEntityContext } = useLiaFloat()
  const recentItems = useRecentItemsStore((s) => s.items)

  const CONTEXT_MODES = [
    {
      type: "general" as const,
      label: t('modeGeneral'),
      description: t('modeGeneralDesc'),
      icon: MessageSquare,
    },
    {
      type: "job_chat" as const,
      label: t('modeJob'),
      description: t('modeJobDesc'),
      icon: Briefcase,
    },
    {
      type: "talent_chat" as const,
      label: t('modeCandidate'),
      description: t('modeCandidateDesc'),
      icon: Users,
    },
  ]

  const recentJobs = useMemo(
    () => recentItems.filter((i) => i.type === "vaga").slice(0, 5),
    [recentItems]
  )

  const recentCandidates = useMemo(
    () => recentItems.filter((i) => i.type === "candidato").slice(0, 5),
    [recentItems]
  )

  if (!isOpen) return null

  const activeEntity = entityContext?.type
    ? `${entityContext.type === "job" ? t('entityJob') : t('entityCandidate')}: ${entityContext.name || entityContext.id}`
    : null

  const handleSelectMode = (type: typeof chatContextType) => {
    if (type === "general") {
      setEntityContext(null)
    }
    switchChatContext(type)
  }

  const handleSelectJob = (item: (typeof recentJobs)[0]) => {
    setEntityContext({
      type: "job",
      id: item.meta?.jobId || item.id,
      name: item.title,
    })
    switchChatContext("job_chat")
    onClose()
  }

  const handleSelectCandidate = (item: (typeof recentCandidates)[0]) => {
    setEntityContext({
      type: "candidate",
      id: item.meta?.candidateId || item.id,
      name: item.title,
    })
    switchChatContext("talent_chat")
    onClose()
  }

  const handleClearContext = () => {
    setEntityContext(null)
    switchChatContext("general")
    onClose()
  }

  return (
    <>
      <div className="fixed inset-0 z-40" onClick={onClose} />
      <div
        className={cn(
          "absolute left-0 bottom-full mb-1 z-50 rounded-xl border border-lia-border-subtle bg-lia-bg-primary shadow-lia-lg",
          mode === "fullscreen" ? "w-80" : "w-72"
        )}
      >
        <div className="flex items-center justify-between px-3 pt-3 pb-2">
          <span className="text-xs font-medium text-lia-text-secondary uppercase tracking-wide">
            {t('title')}
          </span>
          <button
            onClick={onClose}
            className="p-0.5 rounded hover:bg-lia-interactive-hover text-lia-text-tertiary hover:text-lia-text-secondary"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="mx-3 mb-2 flex items-start gap-2 px-2.5 py-2 rounded-lg bg-lia-bg-secondary">
          <HelpCircle className="w-3.5 h-3.5 flex-shrink-0 text-lia-text-tertiary mt-px" />
          <p className="text-[11px] text-lia-text-tertiary leading-relaxed">
            {t('helpText')}
          </p>
        </div>

        {activeEntity && (
          <div className="mx-3 mb-2 flex items-center justify-between gap-2 px-2.5 py-1.5 rounded-lg bg-lia-bg-secondary border border-lia-border-subtle">
            <span className="text-xs text-lia-info-color truncate">{activeEntity}</span>
            <button
              onClick={handleClearContext}
              className="text-xs text-lia-text-tertiary hover:text-lia-text-secondary whitespace-nowrap"
            >
              {t('clearContext')}
            </button>
          </div>
        )}

        <div className="px-1.5 pb-1.5">
          {CONTEXT_MODES.map(({ type, label, description, icon: Icon }) => {
            const isActive = chatContextType === type
            return (
              <button
                key={type}
                onClick={() => handleSelectMode(type)}
                className={cn(
                  "w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-left transition-colors",
                  isActive
                    ? "bg-lia-interactive-active text-lia-text-primary"
                    : "text-lia-text-secondary hover:bg-lia-bg-secondary"
                )}
              >
                <Icon className={cn("w-4 h-4 flex-shrink-0", isActive ? "text-lia-info-color" : "")} />
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium">{label}</div>
                  <div className="text-[11px] text-lia-text-tertiary">{description}</div>
                </div>
                {isActive && <div className="w-1.5 h-1.5 rounded-full bg-lia-info-color flex-shrink-0" />}
              </button>
            )
          })}
        </div>

        {(chatContextType === "job_chat" || chatContextType === "general") && recentJobs.length > 0 && (
          <div className="border-t border-lia-border-subtle px-1.5 pt-1.5 pb-1.5">
            <span className="px-2.5 text-[11px] font-medium text-lia-text-tertiary uppercase tracking-wide">
              {t('recentJobs')}
            </span>
            {recentJobs.map((job) => (
              <button
                key={job.id}
                onClick={() => handleSelectJob(job)}
                className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-left text-sm text-lia-text-secondary hover:bg-lia-bg-secondary transition-colors"
              >
                <Briefcase className="w-3.5 h-3.5 flex-shrink-0 text-lia-text-tertiary" />
                <span className="truncate flex-1">{job.title}</span>
                <ChevronRight className="w-3 h-3 text-lia-text-disabled flex-shrink-0" />
              </button>
            ))}
          </div>
        )}

        {(chatContextType === "talent_chat" || chatContextType === "general") && recentCandidates.length > 0 && (
          <div className="border-t border-lia-border-subtle px-1.5 pt-1.5 pb-1.5">
            <span className="px-2.5 text-[11px] font-medium text-lia-text-tertiary uppercase tracking-wide">
              {t('recentCandidates')}
            </span>
            {recentCandidates.map((cand) => (
              <button
                key={cand.id}
                onClick={() => handleSelectCandidate(cand)}
                className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-left text-sm text-lia-text-secondary hover:bg-lia-bg-secondary transition-colors"
              >
                <Users className="w-3.5 h-3.5 flex-shrink-0 text-lia-text-tertiary" />
                <span className="truncate flex-1">{cand.title}</span>
                <ChevronRight className="w-3 h-3 text-lia-text-disabled flex-shrink-0" />
              </button>
            ))}
          </div>
        )}

        {recentJobs.length === 0 && recentCandidates.length === 0 && (
          <div className="border-t border-lia-border-subtle px-3 py-3">
            <p className="text-xs text-lia-text-tertiary text-center">
              {t('emptyHint')}
            </p>
          </div>
        )}
      </div>
    </>
  )
}
