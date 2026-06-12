/**
 * @deprecated Pre-unified-chat hook. Zero external callers.
 * Canonical: useLiaPanelStore (wizard panel focus) + openDynamicPanel (panel content).
 * This file may be removed in a future cleanup sprint.
 */
"use client"

import React from "react"
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from "@/components/ui/sheet"
import { Button } from "@/components/ui/button"
import { X, Loader2 } from "lucide-react"
import { SidePanelType, PanelSubmitData } from "./types"

import { CompensationBenefitsPanel } from "./panels/CompensationBenefitsPanel"
import { TechnicalRequirementsPanel } from "./panels/TechnicalRequirementsPanel"
import { BehavioralCompetenciesPanel } from "./panels/BehavioralCompetenciesPanel"
import { LanguagesPanel } from "./panels/LanguagesPanel"
import { WSIQuestionsPanel } from "./panels/WSIQuestionsPanel"
import { InterviewSchedulingPanel } from "./panels/InterviewSchedulingPanel"
import { CalibrationFeedbackPanel } from "./panels/CalibrationFeedbackPanel"

interface SidePanelContainerProps {
  isOpen: boolean
  panelType: SidePanelType | null
  title?: string
  initialData?: Record<string, unknown>
  isLoading?: boolean
  onClose: () => void
  onSubmit: (data: PanelSubmitData) => Promise<void>
}

const PANEL_ICONS: Record<SidePanelType, string> = {
  compensation_benefits: "💰",
  technical_requirements: "💻",
  behavioral_competencies: "🧠",
  languages: "🌍",
  benefits_detailed: "🎁",
  wsi_questions: "📝",
  interview_scheduling: "📅",
  candidate_evaluation: "⭐",
  calibration_feedback: "🎯",
  job_requirements: "📋",
  candidate_profile: "👤",
  search_filters: "🔍",
  ats_field_mapping: "🔗",
  ats_sync_status: "🔄",
  email_composer: "📧",
  whatsapp_composer: "💬"
}

const PANEL_TITLES: Record<SidePanelType, string> = {
  compensation_benefits: "Remuneração e Benefícios",
  technical_requirements: "Requisitos Técnicos",
  behavioral_competencies: "Competências Comportamentais",
  languages: "Idiomas",
  benefits_detailed: "Benefícios Detalhados",
  wsi_questions: "Perguntas WSI",
  interview_scheduling: "Agendar Entrevista",
  candidate_evaluation: "Avaliação do Candidato",
  calibration_feedback: "Calibração de Busca",
  job_requirements: "Requisitos da Vaga",
  candidate_profile: "Perfil do Candidato",
  search_filters: "Filtros de Busca",
  ats_field_mapping: "Mapeamento ATS",
  ats_sync_status: "Status de Sincronização",
  email_composer: "Compor E-mail",
  whatsapp_composer: "Compor WhatsApp"
}

export function SidePanelContainer({
  isOpen,
  panelType,
  title,
  initialData = {},
  isLoading = false,
  onClose,
  onSubmit
}: SidePanelContainerProps) {
  const handleSubmit = async (data: unknown) => {
    if (!panelType) return
    await onSubmit({
      panel_type: panelType,
      data: data as PanelSubmitData["data"]
    })
  }

  const renderPanel = () => {
    if (!panelType) return null

    switch (panelType) {
      case "compensation_benefits":
        return (
          <CompensationBenefitsPanel
            initialData={initialData}
            onSubmit={handleSubmit}
            isLoading={isLoading}
          />
        )
      case "technical_requirements":
        return (
          <TechnicalRequirementsPanel
            initialData={initialData}
            onSubmit={handleSubmit}
            isLoading={isLoading}
          />
        )
      case "behavioral_competencies":
        return (
          <BehavioralCompetenciesPanel
            initialData={initialData}
            onSubmit={handleSubmit}
            isLoading={isLoading}
          />
        )
      case "languages":
        return (
          <LanguagesPanel
            initialData={initialData}
            onSubmit={handleSubmit}
            isLoading={isLoading}
          />
        )
      case "wsi_questions":
        return (
          <WSIQuestionsPanel
            initialData={initialData}
            onSubmit={handleSubmit}
            isLoading={isLoading}
          />
        )
      case "interview_scheduling":
        return (
          <InterviewSchedulingPanel
            initialData={initialData}
            onSubmit={handleSubmit}
            isLoading={isLoading}
          />
        )
      case "calibration_feedback":
        return (
          <CalibrationFeedbackPanel
            initialData={initialData}
            onSubmit={handleSubmit}
            isLoading={isLoading}
          />
        )
      default:
        return (
          <div className="flex flex-col items-center justify-center h-64 text-lia-text-tertiary">
            <p>Painel "{panelType}" em desenvolvimento</p>
          </div>
        )
    }
  }

  const displayTitle = title || (panelType ? PANEL_TITLES[panelType] : "")
  const icon = panelType ? PANEL_ICONS[panelType] : ""

  return (
    <Sheet open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <SheetContent 
        side="right" 
        className="w-panel-xl sm:max-w-panel-xl overflow-y-auto rounded-xl dark:bg-lia-bg-secondary dark:border-lia-border-subtle"
      >
        <SheetHeader className="pb-4 dark:border-lia-border-subtle">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-2xl">{icon}</span>
              <SheetTitle className="text-xl font-semibold font-sans">
                {displayTitle}
              </SheetTitle>
            </div>
          </div>
          {isLoading && (
            <div className="flex items-center gap-2 text-sm text-lia-text-tertiary mt-2" role="status" aria-live="polite" aria-label="Carregando...">
              <Loader2 className="h-4 w-4 animate-spin motion-reduce:animate-none" />
              Salvando...
            </div>
          )}
        </SheetHeader>
        
        <div className="py-6">
          {renderPanel()}
        </div>
      </SheetContent>
    </Sheet>
  )
}
