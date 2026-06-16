"use client"

import React from "react"
import { Activity, CheckCircle2, XCircle, AlertTriangle, Clock } from "lucide-react"
import { useTranslations } from "next-intl"
import { cn } from "@/lib/utils"
import { badgeStyles } from "@/lib/design-tokens"

/**
 * Activity feed item canonical (timeline) — Wave B2.2 (2026-05-27).
 *
 * Renderiza um item da resposta de
 *   GET /api/backend-proxy/agent-monitoring/agents/{id}/activities
 * (ActivityResponse do backend FastAPI).
 *
 * Compacto, sem cyan, alinhado ao DESIGN.md "Quiet Operator" (90/10 Rule).
 */

export interface AgentActivityItem {
  id: string
  agent_id: string
  agent_name?: string
  type: string
  title: string
  description?: string | null
  status?: string | null
  started_at?: string | null
  completed_at?: string | null
  duration_seconds?: number | null
  sla_breach?: boolean | null
  related_job_id?: string | null
  related_candidate_id?: string | null
}

interface AgentActivityCardProps {
  activity: AgentActivityItem
}

const STATUS_ICON: Record<string, React.ReactNode> = {
  success: <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" aria-hidden="true" />,
  failed: <XCircle className="w-3.5 h-3.5 text-red-600" aria-hidden="true" />,
  warning: <AlertTriangle className="w-3.5 h-3.5 text-amber-600" aria-hidden="true" />,
  in_progress: <Clock className="w-3.5 h-3.5 text-lia-text-secondary" aria-hidden="true" />,
}

function formatRelativeTime(iso: string | null | undefined, locale = "pt-BR"): string {
  if (!iso) return ""
  const d = new Date(iso)
  const diffMs = Date.now() - d.getTime()
  const diffMin = Math.floor(diffMs / 60_000)
  if (diffMin < 1) return locale.startsWith("pt") ? "agora" : "now"
  if (diffMin < 60) return locale.startsWith("pt") ? `${diffMin}min` : `${diffMin}m`
  const diffH = Math.floor(diffMin / 60)
  if (diffH < 24) return locale.startsWith("pt") ? `${diffH}h` : `${diffH}h`
  const diffD = Math.floor(diffH / 24)
  return locale.startsWith("pt") ? `${diffD}d` : `${diffD}d`
}

export function AgentActivityCard({ activity }: AgentActivityCardProps) {
  const t = useTranslations("agents.customAgents")
  const status = activity.status ?? "success"
  const icon = STATUS_ICON[status] ?? <Activity className="w-3.5 h-3.5 text-lia-text-secondary" aria-hidden="true" />
  const time = formatRelativeTime(activity.completed_at || activity.started_at)

  return (
    <div
      className={cn(
        "flex items-start gap-2.5 py-2 px-2 rounded-md",
        "hover:bg-lia-bg-tertiary/40 transition-colors",
      )}
      data-testid="agent-activity-item"
    >
      <div className="flex-shrink-0 mt-0.5">{icon}</div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <p className="text-xs font-medium text-lia-text-primary truncate">{activity.title}</p>
          {activity.sla_breach ? (
            <span className={cn(badgeStyles.default, "text-[10px] bg-amber-50 text-amber-700 border-amber-200")}>
              {t("slaBreach")}
            </span>
          ) : null}
        </div>
        {activity.description ? (
          <p className="text-[11px] text-lia-text-secondary line-clamp-2 mt-0.5">{activity.description}</p>
        ) : null}
      </div>
      {time ? (
        <span className="text-[10px] text-lia-text-muted flex-shrink-0 mt-0.5" aria-label={activity.completed_at || activity.started_at || ""}>
          {time}
        </span>
      ) : null}
    </div>
  )
}
