"use client"

import React from "react"
import { useTranslations } from "next-intl"
import { Bot, User, RefreshCw, Search, Download } from "lucide-react"
import { Chip, type ChipVariant } from "@/components/ui/chip"

interface CandidateOriginBadgeProps {
  origin: "agent" | "direct" | "pool" | "search" | "import" | "manual"
  detail?: string
  date?: string
  size?: "sm" | "md"
}

const ORIGIN_ICON = {
  agent: Bot,
  direct: User,
  pool: RefreshCw,
  search: Search,
  import: Download,
  manual: User,
}

const ORIGIN_VARIANT: Record<string, { variant: ChipVariant; muted?: boolean }> = {
  agent: { variant: "info" },
  direct: { variant: "neutral", muted: true },
  pool: { variant: "info" },
  search: { variant: "success" },
  import: { variant: "warning" },
  manual: { variant: "neutral", muted: true },
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString(undefined, { day: "2-digit", month: "2-digit" })
  } catch {
    return iso
  }
}

export default function CandidateOriginBadge({
  origin, detail, date, size = "sm",
}: CandidateOriginBadgeProps) {
  const t = useTranslations('agents.candidateOrigin')
  const style = ORIGIN_VARIANT[origin] || ORIGIN_VARIANT.manual
  const Icon = ORIGIN_ICON[origin] || ORIGIN_ICON.manual
  const label = t(`origins.${origin}.label`)
  const tooltipBase = t(`origins.${origin}.tooltip`, { detail: detail || t(`origins.${origin}.defaultDetail`), date: date ? formatDate(date) : "" })
  const tooltip = date ? tooltipBase : tooltipBase.replace(/\s*em\s*$/, "").replace(/\s*on\s*$/, "")
  const iconSize = size === "sm" ? "w-3.5 h-3.5" : "w-4 h-4"

  return (
    <Chip
      density={size === "sm" ? "compact" : "comfortable"}
      variant={style.variant}
      muted={style.muted}
      title={tooltip}
    >
      <Icon className={iconSize} />
      {size === "md" && <span>{label}</span>}
    </Chip>
  )
}
