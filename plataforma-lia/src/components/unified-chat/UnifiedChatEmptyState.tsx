"use client"

import React from "react"
import { Brain, Building, FileSpreadsheet, Globe } from "lucide-react"
import { cn } from "@/lib/utils"
import type { ChatMode } from "./unified-chat-types"
import { ChatWorkflowReels } from "@/components/ui/chat-workflow-reels"
import { useTranslations } from 'next-intl'
import type { ChatContextType } from "@/contexts/lia-float-context"

interface Props {
  mode: ChatMode
  onSuggestionClick: (prompt: string) => void
  contextType?: ChatContextType
}

const SETTINGS_CHIPS = [
  { label: "Completar perfil da empresa", command: "Quero completar o perfil da minha empresa", icon: Building },
  { label: "Importar planilha", command: "Quero importar uma planilha de colaboradores", icon: FileSpreadsheet },
  { label: "Analisar website", command: "Analise o website da minha empresa e extraia informacoes", icon: Globe },
]

export function UnifiedChatEmptyState({ mode, onSuggestionClick, contextType }: Props) {
  const isCompact = mode === "sidebar" || mode === "floating"
  const t = useTranslations('chat')

  if (contextType === "settings_config") {
    return (
      <div className={cn(
        "flex flex-col items-center justify-center flex-1 px-6",
        isCompact ? "py-8 gap-4" : "py-12 gap-6"
      )}>
        <div className={cn(
          "rounded-full border border-lia-border-subtle flex items-center justify-center bg-lia-bg-primary",
          isCompact ? "w-12 h-12" : "w-16 h-16"
        )}>
          <Building
            className={cn("text-wedo-cyan", isCompact ? "w-6 h-6" : "w-8 h-8")}
            strokeWidth={1.5}
          />
        </div>

        <h2 className={cn(
          "font-semibold text-lia-text-primary text-center",
          isCompact ? "text-base" : "text-xl"
        )}>
          Configure sua empresa
        </h2>
        <p className="text-sm text-lia-text-secondary text-center max-w-[280px]">
          Me conte sobre sua empresa e eu vou preencher os dados automaticamente.
        </p>

        <div className={cn("w-full flex flex-col gap-2", isCompact ? "max-w-[280px]" : "max-w-[400px]")}>
          {SETTINGS_CHIPS.map((chip) => (
            <button
              key={chip.command}
              onClick={() => onSuggestionClick(chip.command)}
              className="flex items-center gap-3 p-3 rounded-xl text-left border border-lia-border-subtle bg-lia-bg-primary hover:bg-lia-bg-secondary hover:border-wedo-cyan/30 transition-all"
            >
              <div className="p-1.5 rounded-lg bg-wedo-cyan/10 text-wedo-cyan flex-shrink-0">
                <chip.icon className="w-4 h-4" />
              </div>
              <span className="text-sm font-medium text-lia-text-primary">{chip.label}</span>
            </button>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className={cn(
      "flex flex-col items-center justify-center flex-1 px-6",
      isCompact ? "py-8 gap-4" : "py-12 gap-6"
    )}>
      <div className={cn(
        "rounded-full border border-lia-border-subtle flex items-center justify-center bg-lia-bg-primary",
        isCompact ? "w-12 h-12" : "w-16 h-16"
      )}>
        <Brain
          className={cn("text-wedo-cyan", isCompact ? "w-6 h-6" : "w-8 h-8")}
          strokeWidth={1.5}
        />
      </div>

      <h2 className={cn(
        "font-semibold text-lia-text-primary text-center",
        isCompact ? "text-base" : "text-xl"
      )}>
        {t("greeting")}
      </h2>

      <div className={cn(
        "w-full",
        isCompact ? "max-w-[280px]" : "max-w-[640px]"
      )}>
        <ChatWorkflowReels
          onSelect={onSuggestionClick}
          compact={isCompact}
        />
      </div>
    </div>
  )
}
