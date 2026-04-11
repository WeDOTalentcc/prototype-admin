"use client"

import React, { useState } from "react"
import { Bot, ChevronRight, Zap } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  textStyles, cardStyles, badgeStyles, buttonStyles
} from "@/lib/design-tokens"

/**
 * WizardAgentStep — Step 3 of the Job Wizard.
 *
 * Offers the recruiter the option to activate a sourcing agent for the job.
 * If accepted, shows quick preferences and triggers calibration after wizard completes.
 *
 * Integration:
 *   In the job wizard, render this as step 3 (after WSI + screening questions):
 *
 *   <WizardAgentStep
 *     jobTitle="Backend Sênior"
 *     onActivate={(config) => { setSourcingConfig(config); goToNextStep(); }}
 *     onSkip={() => goToNextStep()}
 *   />
 */

interface WizardAgentStepProps {
  jobTitle: string
  onActivate: (config: AgentWizardConfig) => void
  onSkip: () => void
}

interface AgentWizardConfig {
  enabled: boolean
  sectorTemplate: string | null
  candidatesPerDay: number
  notifyFrequency: string
  channels: string[]
  shouldCalibrate: boolean
}

const SECTOR_OPTIONS = [
  { id: "technology", label: "Tecnologia", icon: "💻" },
  { id: "manufacturing", label: "Manufatura", icon: "🏭" },
  { id: "healthcare", label: "Saúde", icon: "🏥" },
  { id: "retail", label: "Varejo", icon: "🛒" },
  { id: "transportation", label: "Transporte", icon: "🚛" },
]

export default function WizardAgentStep({ jobTitle, onActivate, onSkip }: WizardAgentStepProps) {
  const [wantsAgent, setWantsAgent] = useState<boolean | null>(null)
  const [sectorTemplate, setSectorTemplate] = useState<string | null>(null)
  const [candidatesPerDay, setCandidatesPerDay] = useState(20)
  const [notifyFrequency, setNotifyFrequency] = useState("daily")

  if (wantsAgent === null) {
    // Initial prompt
    return (
      <div className="space-y-6">
        <div className="text-center">
          <Bot className="w-12 h-12 text-lia-text-tertiary mx-auto mb-3" />
          <h3 className={textStyles.h3}>Sourcing Automático</h3>
          <p className={`${textStyles.body} mt-2 max-w-md mx-auto`}>
            Quer que um agente busque candidatos automaticamente para esta vaga?
            Ele aprende com seu feedback e melhora a cada ciclo.
          </p>
        </div>

        <div className="flex justify-center gap-4">
          <Button className={buttonStyles.primary} onClick={() => setWantsAgent(true)}>
            <Zap className="w-4 h-4 mr-1" />
            Sim, ativar sourcing
          </Button>
          <Button className={buttonStyles.secondary} onClick={onSkip}>
            Não, vou buscar manualmente
          </Button>
        </div>
      </div>
    )
  }

  // Configuration
  return (
    <div className="space-y-6 max-w-lg mx-auto">
      <div>
        <h3 className={textStyles.h3}>Configurar Agente — {jobTitle}</h3>
        <p className={textStyles.caption}>Escolha um template e ajuste as preferências.</p>
      </div>

      {/* Sector template selection */}
      <div>
        <label className={textStyles.label}>Template de setor</label>
        <div className="grid grid-cols-3 gap-2 mt-2">
          {SECTOR_OPTIONS.map(s => (
            <button
              key={s.id}
              onClick={() => setSectorTemplate(s.id === sectorTemplate ? null : s.id)}
              className={`p-3 rounded-md border text-center text-sm transition-colors ${
                sectorTemplate === s.id
                  ? "border-lia-text-primary bg-lia-bg-secondary text-lia-text-primary"
                  : "border-lia-border-subtle text-lia-text-secondary hover:bg-lia-bg-secondary"
              }`}
            >
              <span className="text-lg">{s.icon}</span>
              <p className="mt-1">{s.label}</p>
            </button>
          ))}
          <button
            onClick={() => setSectorTemplate(null)}
            className={`p-3 rounded-md border text-center text-sm transition-colors ${
              sectorTemplate === null
                ? "border-lia-text-primary bg-lia-bg-secondary text-lia-text-primary"
                : "border-lia-border-subtle text-lia-text-secondary hover:bg-lia-bg-secondary"
            }`}
          >
            <span className="text-lg">✨</span>
            <p className="mt-1">Auto</p>
          </button>
        </div>
      </div>

      {/* Candidates per day */}
      <div>
        <label className={textStyles.label}>Candidatos por dia</label>
        <div className="flex gap-2 mt-2">
          {[10, 20, 30, 50].map(n => (
            <button
              key={n}
              onClick={() => setCandidatesPerDay(n)}
              className={`px-4 py-2 rounded-md text-sm border transition-colors ${
                candidatesPerDay === n
                  ? "border-lia-text-primary bg-lia-bg-secondary text-lia-text-primary"
                  : "border-lia-border-subtle text-lia-text-secondary hover:bg-lia-bg-secondary"
              }`}
            >
              {n}
            </button>
          ))}
        </div>
      </div>

      {/* Notify frequency */}
      <div>
        <label className={textStyles.label}>Notificações</label>
        <div className="flex gap-2 mt-2">
          {[
            { id: "realtime", label: "Tempo real" },
            { id: "daily", label: "Resumo diário" },
            { id: "weekly", label: "Semanal" },
          ].map(opt => (
            <button
              key={opt.id}
              onClick={() => setNotifyFrequency(opt.id)}
              className={`px-4 py-2 rounded-md text-sm border transition-colors ${
                notifyFrequency === opt.id
                  ? "border-lia-text-primary bg-lia-bg-secondary text-lia-text-primary"
                  : "border-lia-border-subtle text-lia-text-secondary hover:bg-lia-bg-secondary"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* Actions */}
      <div className="flex justify-between pt-4 border-t border-lia-border-subtle">
        <Button className={buttonStyles.secondary} onClick={() => setWantsAgent(null)}>
          Voltar
        </Button>
        <Button
          className={buttonStyles.primary}
          onClick={() => onActivate({
            enabled: true,
            sectorTemplate,
            candidatesPerDay,
            notifyFrequency,
            channels: ["internal", "linkedin"],
            shouldCalibrate: true,
          })}
        >
          Ativar e Calibrar <ChevronRight className="w-4 h-4 ml-1" />
        </Button>
      </div>

      <p className={`${textStyles.caption} text-center`}>
        Após publicar a vaga, o Big Card de calibração aparecerá para você avaliar 3+ perfis.
      </p>
    </div>
  )
}
