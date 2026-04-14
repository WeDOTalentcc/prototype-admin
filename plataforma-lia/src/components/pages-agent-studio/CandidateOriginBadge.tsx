"use client"

import React from "react"
import { useTranslations } from "next-intl"
import { Bot, User, RefreshCw, Search, Download } from "lucide-react"
import { textStyles } from "@/lib/design-tokens"

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

const ORIGIN_STYLE = {
  agent: { bgColor: "bg-purple-50", textColor: "text-purple-700" },
  direct: { bgColor: "bg-lia-bg-secondary", textColor: "text-lia-text-secondary" },
  pool: { bgColor: "bg-blue-50", textColor: "text-blue-700" },
  search: { bgColor: "bg-green-50", textColor: "text-green-700" },
  import: { bgColor: "bg-yellow-50", textColor: "text-yellow-700" },
  manual: { bgColor: "bg-lia-bg-secondary", textColor: "text-lia-text-secondary" },
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
  const style = ORIGIN_STYLE[origin] || ORIGIN_STYLE.manual
  const Icon = ORIGIN_ICON[origin] || ORIGIN_ICON.manual
  const label = t(`origins.${origin}.label`)
  const tooltipBase = t(`origins.${origin}.tooltip`, { detail: detail || t(`origins.${origin}.defaultDetail`), date: date ? formatDate(date) : "" })
  const tooltip = date ? tooltipBase : tooltipBase.replace(/\s*em\s*$/, "").replace(/\s*on\s*$/, "")
  const iconSize = size === "sm" ? "w-3.5 h-3.5" : "w-4 h-4"

  return (
    <span
      className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded ${style.bgColor} ${style.textColor}`}
      title={tooltip}
    >
      <Icon className={iconSize} />
      {size === "md" && <span className={textStyles.caption}>{label}</span>}
    </span>
  )
}
