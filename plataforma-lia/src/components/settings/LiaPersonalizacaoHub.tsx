"use client"

/**
 * LiaPersonalizacaoHub — hub de configuracao da IA por tenant.
 *
 * Agrupa em um unico hub as 4 surfaces de personalizacao:
 * - Persona: nome + tom da IA (AiPersonaPanel)
 * - Instrucoes por campo: 34 toggles de campo + instrucoes custom (LiaFieldsConfigPanel)
 * - Learning Loops: retroalimentacao do modelo (LearningLoopsPanel)
 * - Visibilidade: transparencia sobre dados enviados para a IA (LiaImpactSummary)
 *
 * Group: "lia" (P1-7 sidebar reorganization — 2026-05-27)
 * P1-9: tab "Visibilidade" adicionada (2026-05-27) — recruiter transparency panel.
 */

import React, { useState } from "react"
import { Brain } from "lucide-react"
import { AiPersonaPanel } from "./AiPersonaPanel"
import { HiringPoliciesHub } from "./HiringPoliciesHub"
import { LiaFieldsConfigPanel } from "./LiaFieldsConfigPanel"
import { LearningLoopsPanel } from "./LearningLoopsPanel"
import { LiaImpactSummary } from "./lia/LiaImpactSummary"
import { HubHeader } from "./_shared"

const TABS = [
  { id: "persona", label: "Persona da IA" },
  { id: "regras", label: "Regras" },
  { id: "instrucoes-lia", label: "Instrucoes por Campo" },
  { id: "learning-loops", label: "Learning Loops" },
  { id: "visibilidade", label: "Visibilidade" },
] as const

type TabId = typeof TABS[number]["id"]

interface LiaPersonalizacaoHubProps {
  activeSubsection?: string
}

export function LiaPersonalizacaoHub({ activeSubsection }: LiaPersonalizacaoHubProps) {
  const initial = (TABS.find(t => t.id === activeSubsection)?.id ?? "persona") as TabId
  const [activeTab, setActiveTab] = useState<TabId>(initial)

  return (
    <div className="space-y-4" data-testid="hub-lia-personalizacao">
      <HubHeader
        title="Comportamento da LIA"
        description="Persona, regras de processo, instrucoes por campo, learning loops e visibilidade — tudo que governa como a LIA atua."
      />

      {/* Tab nav */}
      <div className="flex gap-1 border-b border-lia-border-subtle dark:border-lia-border-subtle mb-4">
        {TABS.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 text-sm font-medium rounded-t transition-colors ${
              activeTab === tab.id
                ? "bg-lia-bg-tertiary dark:bg-lia-bg-elevated text-lia-text-primary border-b-2 border-lia-btn-primary-bg"
                : "text-lia-text-secondary hover:text-lia-text-primary hover:bg-lia-bg-secondary"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {activeTab === "persona" && <AiPersonaPanel />}
      {activeTab === "regras" && <HiringPoliciesHub embedded />}
      {activeTab === "instrucoes-lia" && <LiaFieldsConfigPanel />}
      {activeTab === "learning-loops" && <LearningLoopsPanel />}
      {activeTab === "visibilidade" && <LiaImpactSummary />}
    </div>
  )
}
