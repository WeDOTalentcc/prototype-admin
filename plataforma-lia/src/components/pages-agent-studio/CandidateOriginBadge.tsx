"use client"

import React from "react"
import { Bot, User, RefreshCw, Search, Download } from "lucide-react"
import { textStyles } from "@/lib/design-tokens"

/**
 * CandidateOriginBadge — shows how a candidate entered the pipeline.
 *
 * Usage in kanban card or table row:
 *   <CandidateOriginBadge origin="agent" detail="Agente Backend v3" date="2026-04-05" />
 *
 * Follows design system: lucide-react icons + design tokens.
 * Tooltips mandatory per plan requirements.
 */

interface CandidateOriginBadgeProps {
  origin: "agent" | "direct" | "pool" | "search" | "import" | "manual"
  detail?: string   // e.g. "Agente Backend v3" or "Pool Motoristas SP"
  date?: string     // ISO date
  size?: "sm" | "md"
}

const ORIGIN_CONFIG = {
  agent: {
    icon: Bot,
    label: "Agente",
    bgColor: "bg-purple-50",
    textColor: "text-purple-700",
    buildTooltip: (detail?: string, date?: string) =>
      `Sourciado pelo ${detail || "Agente"}${date ? ` em ${formatDate(date)}` : ""}`,
  },
  direct: {
    icon: User,
    label: "Direto",
    bgColor: "bg-gray-50",
    textColor: "text-gray-700",
    buildTooltip: (_detail?: string, date?: string) =>
      `Aplicou diretamente${date ? ` em ${formatDate(date)}` : ""}`,
  },
  pool: {
    icon: RefreshCw,
    label: "Pool",
    bgColor: "bg-blue-50",
    textColor: "text-blue-700",
    buildTooltip: (detail?: string, date?: string) =>
      `Migrado do ${detail || "Banco de Talentos"}${date ? ` em ${formatDate(date)}` : ""}`,
  },
  search: {
    icon: Search,
    label: "Busca",
    bgColor: "bg-green-50",
    textColor: "text-green-700",
    buildTooltip: (_detail?: string, date?: string) =>
      `Encontrado via busca${date ? ` em ${formatDate(date)}` : ""}`,
  },
  import: {
    icon: Download,
    label: "Importado",
    bgColor: "bg-yellow-50",
    textColor: "text-yellow-700",
    buildTooltip: (_detail?: string, date?: string) =>
      `Importado${date ? ` em ${formatDate(date)}` : ""}`,
  },
  manual: {
    icon: User,
    label: "Manual",
    bgColor: "bg-gray-50",
    textColor: "text-gray-700",
    buildTooltip: (_detail?: string, date?: string) =>
      `Adicionado manualmente${date ? ` em ${formatDate(date)}` : ""}`,
  },
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" })
  } catch {
    return iso
  }
}

export default function CandidateOriginBadge({
  origin, detail, date, size = "sm",
}: CandidateOriginBadgeProps) {
  const config = ORIGIN_CONFIG[origin] || ORIGIN_CONFIG.manual
  const Icon = config.icon
  const tooltip = config.buildTooltip(detail, date)
  const iconSize = size === "sm" ? "w-3.5 h-3.5" : "w-4 h-4"

  return (
    <span
      className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded ${config.bgColor} ${config.textColor}`}
      title={tooltip}
    >
      <Icon className={iconSize} />
      {size === "md" && <span className={textStyles.caption}>{config.label}</span>}
    </span>
  )
}
