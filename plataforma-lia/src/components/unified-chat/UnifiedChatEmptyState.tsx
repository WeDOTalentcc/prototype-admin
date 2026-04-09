"use client"

import React from "react"
import { Brain, Search, Briefcase, Users, BarChart2 } from "lucide-react"
import { cn } from "@/lib/utils"
import type { ChatMode } from "./unified-chat-types"

interface SuggestionItem {
  icon: React.ElementType
  label: string
  prompt: string
}

const SUGGESTIONS: SuggestionItem[] = [
  {
    icon: Search,
    label: "Buscar candidatos",
    prompt: "Buscar desenvolvedores Python sênior em São Paulo",
  },
  {
    icon: Briefcase,
    label: "Criar nova vaga",
    prompt: "Criar uma vaga de Product Manager",
  },
  {
    icon: Users,
    label: "Analisar pipeline",
    prompt: "Como está o funil das vagas abertas?",
  },
  {
    icon: BarChart2,
    label: "Gerar relatório",
    prompt: "Gerar relatório semanal de recrutamento",
  },
]

interface Props {
  mode: ChatMode
  onSuggestionClick: (prompt: string) => void
}

export function UnifiedChatEmptyState({ mode, onSuggestionClick }: Props) {
  const isCompact = mode === "sidebar" || mode === "floating"

  return (
    <div className={cn(
      "flex flex-col items-center justify-center flex-1 px-6",
      isCompact ? "py-8 gap-4" : "py-16 gap-6"
    )}>
      {/* LIA Avatar */}
      <div className={cn(
        "rounded-full border border-lia-border-subtle flex items-center justify-center bg-lia-bg-primary",
        isCompact ? "w-12 h-12" : "w-16 h-16"
      )}>
        <Brain
          className={cn("text-wedo-cyan", isCompact ? "w-6 h-6" : "w-8 h-8")}
          strokeWidth={1.5}
        />
      </div>

      {/* Greeting */}
      <h2 className={cn(
        "font-semibold text-lia-text-primary text-center font-['Open_Sans',sans-serif]",
        isCompact ? "text-base" : "text-xl"
      )}>
        Como posso ajudar hoje?
      </h2>

      {/* Suggestion Cards */}
      <div className={cn(
        "w-full",
        isCompact
          ? "flex flex-col gap-2 max-w-[280px]"
          : "grid grid-cols-2 gap-3 max-w-[480px]"
      )}>
        {SUGGESTIONS.map((item) => (
          <button
            key={item.label}
            onClick={() => onSuggestionClick(item.prompt)}
            className={cn(
              "group flex items-center gap-3 text-left rounded-md border border-lia-border-subtle",
              "bg-lia-bg-primary hover:bg-lia-bg-secondary",
              "transition-colors motion-reduce:transition-none",
              isCompact ? "px-3 py-2.5" : "px-4 py-3.5"
            )}
          >
            <item.icon className="w-4 h-4 text-lia-text-tertiary group-hover:text-lia-text-secondary flex-shrink-0" />
            <span className="text-sm text-lia-text-secondary group-hover:text-lia-text-primary font-['Open_Sans',sans-serif]">
              {item.label}
            </span>
          </button>
        ))}
      </div>
    </div>
  )
}
