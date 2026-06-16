"use client"

import React, { useState, useEffect } from "react"
import { Zap, ArrowRight } from "lucide-react"
import { textStyles } from "@/lib/design-tokens"

/**
 * VagaProgressBar — shows campaign progress at the top of a job page.
 *
 * Usage:
 *   <VagaProgressBar
 *     jobId={job.id}
 *     onNavigateToStage={(stage) => setActiveTab(stage)}
 *   />
 */

interface VagaProgressBarProps {
  jobId: string | number
  onNavigateToStage?: (stage: string) => void
}

interface CampaignStage {
  stage: string
  label: string
  status: "completed" | "in_progress" | "pending"
  candidates_count: number
  checkpoint?: string | null
}

export default function VagaProgressBar({ jobId, onNavigateToStage }: VagaProgressBarProps) {
  const [stages, setStages] = useState<CampaignStage[]>([])
  const [pendingAction, setPendingAction] = useState<string | null>(null)
  const [campaignName, setCampaignName] = useState<string>("")

  useEffect(() => {
    loadCampaign()
  }, [jobId])

  const loadCampaign = async () => {
    try {
      const res = await fetch(`/api/backend-proxy/recruitment-campaigns?job_id=${jobId}&status=active`)
      const data = await res.json()
      const campaigns = data?.data || []
      if (campaigns.length === 0) return

      const campaign = campaigns[0].attributes || campaigns[0]
      setCampaignName(campaign.name)
      setStages(campaign.stages || [])

      const pending = campaign.pending_action
      if (pending?.message) setPendingAction(pending.message)
    } catch {
      // No campaign for this job — don't show bar
    }
  }

  if (stages.length === 0) return null

  const currentStage = stages.find(s => s.status === "in_progress")

  return (
    <div className="px-4 py-2 bg-lia-bg-secondary">
      {/* Stage dots */}
      <div className="flex items-center gap-1">
        {stages.map((stage, i) => {
          const isCompleted = stage.status === "completed"
          const isCurrent = stage.status === "in_progress"

          return (
            <React.Fragment key={stage.stage}>
              <button
                onClick={() => onNavigateToStage?.(stage.stage)}
                className={`flex items-center gap-1 px-2 py-0.5 rounded text-xs transition-colors ${
                  isCompleted ? "bg-lia-bg-inverse text-white"
                  : isCurrent ? "bg-yellow-100 text-yellow-800 ring-1 ring-yellow-300"
                  : "bg-lia-bg-tertiary text-lia-text-tertiary"
                }`}
                title={`${stage.label}${stage.candidates_count > 0 ? ` (${stage.candidates_count})` : ""}`}
              >
                {isCompleted ? "✓" : isCurrent ? "●" : "○"} {stage.label}
                {stage.candidates_count > 0 && (
                  <span className="opacity-70">({stage.candidates_count})</span>
                )}
              </button>
              {i < stages.length - 1 && (
                <div className={`h-px w-2 ${isCompleted ? "bg-lia-bg-inverse" : "bg-lia-interactive-active"}`} />
              )}
            </React.Fragment>
          )
        })}
      </div>

      {/* Pending action */}
      {pendingAction && currentStage && (
        <div className="flex items-center gap-2 mt-1.5">
          <Zap className="w-3 h-3 text-yellow-600" />
          <span className={`${textStyles.caption} text-yellow-800`}>
            {pendingAction}
          </span>
          <button
            onClick={() => onNavigateToStage?.(currentStage.stage)}
            className="flex items-center gap-0.5 text-xs text-yellow-700 font-medium hover:text-yellow-900"
          >
            Ir <ArrowRight className="w-3 h-3" />
          </button>
        </div>
      )}
    </div>
  )
}
