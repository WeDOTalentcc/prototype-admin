"use client"

import { useState } from "react"
import { ChevronDown, ChevronUp } from "lucide-react"
import type { WeeklyDigestData } from "./weekly-digest-notification"

interface WeeklyDigestTeamsCardProps {
  digest: WeeklyDigestData
  recruiterName?: string
  onViewInChat?: () => void
}

type SectionKey = "pipeline" | "risk" | "compliance" | "optimization"

export function WeeklyDigestTeamsCard({
  digest,
  recruiterName = "Ana",
  onViewInChat,
}: WeeklyDigestTeamsCardProps) {
  const [openSection, setOpenSection] = useState<SectionKey | null>("pipeline")

  const toggle = (key: SectionKey) => setOpenSection(openSection === key ? null : key)

  return (
    <div className="w-full max-w-[560px]">
      <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-lg shadow-lia-md border border-lia-border-subtle overflow-hidden">
        <div className="h-1 bg-[#6264A7]" />

        <div className="p-5">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-9 h-9 rounded-full bg-[#6264A7] flex items-center justify-center text-white text-sm font-semibold">
              LIA
            </div>
            <div>
              <p className="text-sm font-semibold text-lia-text-primary">LIA — Assistente de Recrutamento</p>
              <p className="text-xs text-lia-text-tertiary">Resumo Semanal · {digest.date}</p>
            </div>
          </div>

          <h2 className="text-base font-semibold text-lia-text-primary mb-1">
            Resumo Semanal — Suas Vagas
          </h2>
          <p className="text-sm text-lia-text-secondary mb-4">
            Olá {recruiterName}, aqui está o panorama da sua semana de recrutamento.
          </p>

          <div className="border border-lia-border-subtle rounded-lg mb-3 overflow-hidden">
            <button
              className="w-full flex items-center justify-between p-3 bg-lia-bg-secondary hover:bg-lia-interactive-active transition-colors text-left"
              onClick={() => toggle("pipeline")}
            >
              <div className="flex items-center gap-2">
                <span className="text-[#6264A7] text-lg">📊</span>
                <span className="text-sm font-medium text-lia-text-primary">Saúde do Pipeline</span>
              </div>
              {openSection === "pipeline"
                ? <ChevronUp className="w-4 h-4 text-lia-text-tertiary" />
                : <ChevronDown className="w-4 h-4 text-lia-text-tertiary" />}
            </button>
            {openSection === "pipeline" && (
              <div className="p-3 border-t border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary">
                <div className="grid grid-cols-3 gap-3 mb-3">
                  <div className="text-center">
                    <p className="text-2xl font-semibold text-[#6264A7]">{digest.pipeline.activeJobs}</p>
                    <p className="text-xs text-lia-text-tertiary">vagas ativas</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-semibold text-status-success">{digest.pipeline.screened}</p>
                    <p className="text-xs text-lia-text-tertiary">candidatos triados</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-semibold text-status-warning">{digest.pipeline.interviews}</p>
                    <p className="text-xs text-lia-text-tertiary">entrevistas agendadas</p>
                  </div>
                </div>
                {digest.pipeline.conversionRate != null && (
                  <p className="text-sm text-lia-text-secondary">
                    Taxa de conversão triagem→entrevista: {digest.pipeline.conversionRate}%
                    {digest.pipeline.conversionDelta != null && digest.pipeline.conversionDelta > 0 && (
                      <span className="text-status-success"> (+{digest.pipeline.conversionDelta}%)</span>
                    )}
                  </p>
                )}
              </div>
            )}
          </div>

          {digest.atRiskJobs.length > 0 && (
            <div className="border border-lia-border-subtle rounded-lg mb-3 overflow-hidden">
              <button
                className="w-full flex items-center justify-between p-3 bg-lia-bg-secondary hover:bg-lia-interactive-active transition-colors text-left"
                onClick={() => toggle("risk")}
              >
                <div className="flex items-center gap-2">
                  <span className="text-lg">⚠️</span>
                  <span className="text-sm font-medium text-lia-text-primary">Vagas em Risco</span>
                  <span className="bg-status-warning/15 text-status-warning text-micro font-medium px-2 py-0.5 rounded-full">
                    {digest.atRiskJobs.length}
                  </span>
                </div>
                {openSection === "risk"
                  ? <ChevronUp className="w-4 h-4 text-lia-text-tertiary" />
                  : <ChevronDown className="w-4 h-4 text-lia-text-tertiary" />}
              </button>
              {openSection === "risk" && (
                <div className="p-3 border-t border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary space-y-2">
                  {digest.atRiskJobs.map((job, i) => (
                    <div key={i} className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-lia-text-primary">{job.title} — {job.company}</p>
                        <p className="text-xs text-lia-text-tertiary">
                          {job.detail || `Time-to-fill: ${job.daysOpen} dias (meta: ${job.targetDays})`}
                        </p>
                      </div>
                      <span className={`text-micro font-medium px-2 py-0.5 rounded-full ${
                        job.severity === "critical"
                          ? "bg-status-error/15 text-status-error"
                          : "bg-status-warning/15 text-status-warning"
                      }`}>
                        {job.severity === "critical" ? "crítico" : "atenção"}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          <div className="border border-lia-border-subtle rounded-lg mb-3 overflow-hidden">
            <button
              className="w-full flex items-center justify-between p-3 bg-lia-bg-secondary hover:bg-lia-interactive-active transition-colors text-left"
              onClick={() => toggle("compliance")}
            >
              <div className="flex items-center gap-2">
                <span className="text-lg">🛡️</span>
                <span className="text-sm font-medium text-lia-text-primary">Compliance e Fairness</span>
                <span className={`text-micro font-medium px-2 py-0.5 rounded-full ${
                  digest.compliance.status === "ok"
                    ? "bg-status-success/15 text-status-success"
                    : "bg-status-warning/15 text-status-warning"
                }`}>
                  {digest.compliance.status === "ok" ? "OK" : "Atenção"}
                </span>
              </div>
              {openSection === "compliance"
                ? <ChevronUp className="w-4 h-4 text-lia-text-tertiary" />
                : <ChevronDown className="w-4 h-4 text-lia-text-tertiary" />}
            </button>
            {openSection === "compliance" && (
              <div className="p-3 border-t border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary">
                <p className="text-sm text-lia-text-secondary">{digest.compliance.message}</p>
              </div>
            )}
          </div>

          {digest.optimization && (
            <div className="border border-lia-border-subtle rounded-lg mb-4 overflow-hidden">
              <button
                className="w-full flex items-center justify-between p-3 bg-lia-bg-secondary hover:bg-lia-interactive-active transition-colors text-left"
                onClick={() => toggle("optimization")}
              >
                <div className="flex items-center gap-2">
                  <span className="text-lg">🔬</span>
                  <span className="text-sm font-medium text-lia-text-primary">Otimização e Aprendizado</span>
                </div>
                {openSection === "optimization"
                  ? <ChevronUp className="w-4 h-4 text-lia-text-tertiary" />
                  : <ChevronDown className="w-4 h-4 text-lia-text-tertiary" />}
              </button>
              {openSection === "optimization" && (
                <div className="p-3 border-t border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary">
                  <p className="text-sm text-lia-text-secondary">{digest.optimization.message}</p>
                </div>
              )}
            </div>
          )}

          {onViewInChat && (
            <button
              className="w-full bg-[#6264A7] hover:bg-[#4f5190] text-white text-sm font-medium py-2.5 px-4 rounded transition-colors"
              onClick={onViewInChat}
            >
              Ver detalhes completos no Chat LIA
            </button>
          )}
        </div>

        <div className="px-5 py-3 bg-lia-bg-secondary border-t border-lia-border-subtle">
          <p className="text-xs text-lia-text-tertiary text-center">
            Enviado automaticamente pela LIA · Para desativar, acesse Configurações → Notificações
          </p>
        </div>
      </div>
    </div>
  )
}
