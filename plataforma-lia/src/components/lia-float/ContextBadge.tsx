"use client"

import React from "react"
import { X, Users, Briefcase, LayoutDashboard, Target, Settings, BarChart2, BookOpen, MessageCircle, Brain, type LucideIcon } from "lucide-react"
import { cn } from "@/lib/utils"

export const PAGE_ROUTE_TO_CONTEXT_LABEL: Record<string, string> = {
  candidates: "Funil de Talentos",
  jobs: "Vagas",
  dashboard: "Painel de Controle",
  tasks: "Decidir",
  settings: "Configurações",
  indicators: "Indicadores",
  library: "Biblioteca LIA",
}

export const CONTEXT_PAGE_ICONS: Record<string, LucideIcon> = {
  "Funil de Talentos": Users,
  "Vagas": Briefcase,
  "Painel de Controle": LayoutDashboard,
  "Decidir": Target,
  "Configurações": Settings,
  "Indicadores": BarChart2,
  "Biblioteca LIA": BookOpen,
  "Conversar": MessageCircle,
}

export interface ContextBadgeProps {
  contextPage: string | null | undefined
  onRemove?: () => void
  className?: string
}

export function ContextBadge({ contextPage, onRemove, className }: ContextBadgeProps) {
  if (!contextPage || contextPage === "Conversar") return null

  const Icon = CONTEXT_PAGE_ICONS[contextPage] ?? Brain

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-micro font-medium",
        "border border-lia-border-medium text-lia-text-secondary bg-lia-bg-secondary",
        "flex-shrink-0",
        className
      )}
      aria-label={`Contexto: ${contextPage}`}
    >
      <Icon className="w-3 h-3 text-lia-text-tertiary flex-shrink-0" />
      <span className="truncate max-w-[120px]">{contextPage}</span>
      {onRemove && (
        <button
          type="button"
          onClick={(e) => { e.stopPropagation(); onRemove() }}
          aria-label="Remover contexto"
          className="ml-0.5 flex-shrink-0 hover:text-lia-text-primary text-lia-text-tertiary transition-colors motion-reduce:transition-none"
        >
          <X className="w-2.5 h-2.5" />
        </button>
      )}
    </span>
  )
}
