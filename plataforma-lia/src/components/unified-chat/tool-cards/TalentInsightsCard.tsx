"use client"

/**
 * TalentInsightsCard — inline chat card that opens TalentPoolInsightsModal.
 *
 * Rendered by UnifiedMessageList when backend emits a response_block with
 * type="talent_pool_insights_card". The card shows a summary line and a CTA
 * button that dispatches `lia:open_modal` with modal_id="talent_pool_insights".
 *
 * Design: follows DS v4.2.2 tokens (bg-white, rounded-md, border-gray-200).
 * Pattern: same type-based response_block as search_candidates_result / list_jobs_result.
 *
 * Created 2026-06-17.
 */

import React from "react"
import { BarChart2, ArrowRight } from "lucide-react"
import { cn } from "@/lib/utils"

export interface TalentInsightsCardData {
  job_id: string
  job_title: string
  total_candidates?: number
  conversion_rate?: number
  hiring_probability?: number
}

interface TalentInsightsCardProps {
  data: TalentInsightsCardData
}

export function TalentInsightsCard({ data }: TalentInsightsCardProps) {
  const { job_id, job_title, total_candidates, conversion_rate, hiring_probability } = data

  const handleClick = () => {
    if (typeof window === "undefined") return
    window.dispatchEvent(
      new CustomEvent("lia:open_modal", {
        detail: {
          modal_id: "talent_pool_insights",
          data: { job_id, job_title },
        },
      }),
    )
  }

  // Summary line: show available metrics
  const summaryParts: string[] = []
  if (total_candidates != null) {
    summaryParts.push(`${total_candidates} candidatos`)
  }
  if (conversion_rate != null) {
    summaryParts.push(`${Math.round(conversion_rate)}% conversao`)
  }
  if (hiring_probability != null) {
    summaryParts.push(`${Math.round(hiring_probability)}% prob. contratacao`)
  }
  const summaryText = summaryParts.length > 0
    ? summaryParts.join(" · ")
    : "Dados disponiveis para analise"

  return (
    <div
      className={cn(
        "rounded-md border border-gray-200 bg-white p-3 my-2",
        "dark:border-gray-700 dark:bg-gray-900",
        "shadow-sm transition-colors"
      )}
    >
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-start gap-2.5 min-w-0 flex-1">
          <div className="mt-0.5 flex-shrink-0 rounded-md bg-gray-100 dark:bg-gray-800 p-1.5">
            <BarChart2 className="w-4 h-4 text-gray-600 dark:text-gray-300" />
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
              Talent Pool Insights
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 truncate">
              {job_title} &mdash; {summaryText}
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={handleClick}
          className={cn(
            "shrink-0 inline-flex items-center gap-1",
            "text-xs font-medium px-3 py-1.5 rounded-md",
            "bg-gray-900 text-white hover:bg-gray-800",
            "dark:bg-gray-100 dark:text-gray-900 dark:hover:bg-gray-200",
            "transition-colors focus:outline-none focus:ring-2 focus:ring-gray-400 focus:ring-offset-1"
          )}
        >
          Ver Insights
          <ArrowRight className="w-3 h-3" />
        </button>
      </div>
    </div>
  )
}
