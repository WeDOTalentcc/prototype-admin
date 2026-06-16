"use client"

import React from "react"
import { X, PanelRightClose } from "lucide-react"
import { cn } from "@/lib/utils"
import { useLiaFloat } from "@/contexts/lia-float-context"
import type { DynamicPanelData } from "@/contexts/lia-float-context"
import { CalibrationPanel } from "./CalibrationPanel"
import { CandidateReviewPanel } from "./CandidateReviewPanel"
import { CandidateProfilePanel } from "./CandidateProfilePanel"
import { JobCreationPanel } from "./JobCreationPanel"
import { SchedulingPanel } from "./SchedulingPanel"

interface DynamicContextPanelProps {
  panel: DynamicPanelData
  className?: string
}

const PANEL_TITLES: Record<string, string> = {
  calibration: "Calibração",
  candidate_review: "Review",
  profile: "Perfil",
  job_creation: "Criação de Vaga",
  scheduling: "Agendamento",
}

export function DynamicContextPanel({ panel, className }: DynamicContextPanelProps) {
  const { closeDynamicPanel, updateDynamicPanelData } = useLiaFloat()

  const renderPanel = () => {
    switch (panel.panelType) {
      case "calibration":
        return <CalibrationPanel data={panel.data} onUpdateData={updateDynamicPanelData} />
      case "candidate_review":
        return <CandidateReviewPanel data={panel.data} onUpdateData={updateDynamicPanelData} />
      case "profile":
        return <CandidateProfilePanel data={panel.data} onUpdateData={updateDynamicPanelData} />
      case "job_creation":
        return <JobCreationPanel data={panel.data} onUpdateData={updateDynamicPanelData} />
      case "scheduling":
        return <SchedulingPanel data={panel.data} onUpdateData={updateDynamicPanelData} />
      default:
        return null
    }
  }

  return (
    <div
      className={cn(
        "flex flex-col h-full bg-lia-bg-primary border-l border-lia-border-subtle overflow-hidden",
        "animate-in slide-in-from-right-5 duration-300",
        className
      )}
      role="complementary"
      aria-label={`Painel contextual: ${panel.title || PANEL_TITLES[panel.panelType] || panel.panelType}`}
    >
      <div className="flex items-center justify-between px-3 py-2 flex-shrink-0 bg-lia-bg-secondary">
        <span className="text-micro font-semibold text-lia-text-tertiary uppercase tracking-wider">
          {panel.title || PANEL_TITLES[panel.panelType] || "Contexto"}
        </span>
        <button
          onClick={closeDynamicPanel}
          className="p-1 rounded-md text-lia-text-secondary hover:text-lia-text-primary hover:bg-lia-interactive-hover transition-colors"
          title="Fechar painel"
          aria-label="Fechar painel contextual"
          data-dismiss="true"
        >
          <PanelRightClose className="w-3.5 h-3.5" />
        </button>
      </div>

      <div className="flex-1 overflow-hidden">
        {renderPanel()}
      </div>
    </div>
  )
}
