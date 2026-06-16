"use client"

import React, { useEffect, useRef, useState } from "react"
import { useTranslations } from "next-intl"
import { Megaphone, MegaphoneOff, PauseCircle } from "lucide-react"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"

/**
 * Task #592 — Informative campaign badge for vacancies.
 *
 * "Campanha" = LIA executando uma vaga (sourcing, triagem, contato com
 * candidatos). Esta é apenas a Fase 1 (educativa): o badge sinaliza o estado
 * da campanha para o recrutador entender o vocabulário; pausar/reativar e
 * ações reais virão na Fase 2.
 *
 * Estados:
 *  - "active":  campanha rodando para a vaga
 *  - "paused":  campanha existe mas está pausada
 *  - "none":    sem campanha (ou backend ainda sem o endpoint)
 */
export type JobCampaignStatus = "active" | "paused" | "none"

interface JobCampaignBadgeProps {
  jobId: string | number
  /** When provided, skips the fetch and renders the given status directly. */
  status?: JobCampaignStatus
  /** Compact variant for dense table rows. */
  size?: "sm" | "md"
  className?: string
}

interface CampaignsResponse {
  data?: Array<{
    id: string
    attributes?: {
      status?: string
      job_id?: string | number | null
    }
  }>
  detail?: string
}

// Module-level cache of fetched campaigns by job id, plus a single in-flight
// promise per id to avoid hammering the proxy when many badges mount at once.
const campaignCache = new Map<string, JobCampaignStatus>()
const inflight = new Map<string, Promise<JobCampaignStatus>>()

async function fetchCampaignStatus(jobId: string): Promise<JobCampaignStatus> {
  if (campaignCache.has(jobId)) return campaignCache.get(jobId)!
  const existing = inflight.get(jobId)
  if (existing) return existing

  const promise = (async (): Promise<JobCampaignStatus> => {
    try {
      const res = await fetch(
        `/api/backend-proxy/recruitment-campaigns?job_id=${encodeURIComponent(jobId)}`,
        { headers: { Accept: "application/json" } },
      )
      if (!res.ok) return "none"
      const text = await res.text()
      if (!text) return "none"
      const data: CampaignsResponse = JSON.parse(text)
      // Backend may return `{ detail: "not_implemented" }` while the endpoint
      // is still under construction — degrade to "none" silently.
      if (data?.detail === "not_implemented") return "none"
      const list = Array.isArray(data?.data) ? data.data : []
      if (list.length === 0) return "none"
      const hasActive = list.some(
        (c) => (c.attributes?.status ?? "").toLowerCase() === "active",
      )
      if (hasActive) return "active"
      const hasPaused = list.some(
        (c) => (c.attributes?.status ?? "").toLowerCase() === "paused",
      )
      return hasPaused ? "paused" : "none"
    } catch {
      // Network error / proxy unavailable — treat as no campaign.
      return "none"
    }
  })()

  inflight.set(jobId, promise)
  try {
    const result = await promise
    campaignCache.set(jobId, result)
    return result
  } finally {
    inflight.delete(jobId)
  }
}

export function JobCampaignBadge({
  jobId,
  status: explicitStatus,
  size = "sm",
  className = "",
}: JobCampaignBadgeProps) {
  const t = useTranslations("jobs.campaignBadge")
  const [status, setStatus] = useState<JobCampaignStatus | null>(
    explicitStatus ?? campaignCache.get(String(jobId)) ?? null,
  )
  const cancelledRef = useRef(false)

  useEffect(() => {
    cancelledRef.current = false
    if (explicitStatus) {
      setStatus(explicitStatus)
      return () => {
        cancelledRef.current = true
      }
    }
    const id = String(jobId)
    fetchCampaignStatus(id).then((s) => {
      if (!cancelledRef.current) setStatus(s)
    })
    return () => {
      cancelledRef.current = true
    }
  }, [jobId, explicitStatus])

  // While loading, render nothing — avoids layout flicker in dense lists.
  if (status === null) return null

  const config = STATUS_CONFIG[status]
  const Icon = config.icon
  const label = t(config.labelKey)
  const tooltip = `${label} — ${t("tooltip")}`
  const sizeCls =
    size === "md"
      ? "px-2 py-0.5 text-[11px]"
      : "px-1.5 py-0.5 text-[10px]"
  const iconCls = size === "md" ? "w-3 h-3" : "w-2.5 h-2.5"

  return (
    <TooltipProvider delayDuration={200}>
      <Tooltip>
        <TooltipTrigger asChild>
          <span
            className={`inline-flex items-center gap-1 rounded-full border font-medium whitespace-nowrap ${sizeCls} ${config.classes} ${className}`}
            data-testid="job-campaign-badge"
            data-status={status}
            aria-label={label}
          >
            <Icon className={iconCls} aria-hidden="true" />
            {label}
          </span>
        </TooltipTrigger>
        <TooltipContent side="top" className="max-w-xs text-xs">
          {tooltip}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}

const STATUS_CONFIG: Record<
  JobCampaignStatus,
  { labelKey: "active" | "paused" | "none"; icon: typeof Megaphone; classes: string }
> = {
  active: {
    labelKey: "active",
    icon: Megaphone,
    classes:
      "bg-status-success/10 border-status-success/40 text-status-success",
  },
  paused: {
    labelKey: "paused",
    icon: PauseCircle,
    classes:
      "bg-status-warning/10 border-status-warning/40 text-status-warning",
  },
  none: {
    labelKey: "none",
    icon: MegaphoneOff,
    classes:
      "bg-lia-bg-tertiary border-lia-border-subtle text-lia-text-tertiary",
  },
}
