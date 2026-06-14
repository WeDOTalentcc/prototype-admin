"use client"

import { useState } from "react"
import { ChevronDown, ChevronUp, TrendingUp, TrendingDown, Minus, AlertTriangle, Shield, Lightbulb } from "lucide-react"
import type { WeeklyDigestData } from "./weekly-digest-notification"

interface WeeklyDigestChatMessageProps {
  digest: WeeklyDigestData
  recruiterName?: string
}

type ExpandedSection = "risk" | "metrics" | null

function KpiCell({ value, label, color }: { value: number | string; label: string; color: string }) {
  return (
    <div className="flex flex-col items-center min-w-[64px]">
      <p className={`text-2xl font-semibold ${color}`}>{value}</p>
      <p className="text-[10px] text-lia-text-tertiary mt-0.5">{label}</p>
    </div>
  )
}

function ConversionBar({ rate, delta }: { rate: number; delta?: number | null }) {
  const barWidth = Math.min(Math.max(rate, 0), 100)
  const barColor = rate >= 40 ? "bg-status-success" : rate >= 20 ? "bg-status-warning" : "bg-status-error"
  const DeltaIcon = delta != null && delta > 0 ? TrendingUp : delta != null && delta < 0 ? TrendingDown : Minus
  const deltaColor = delta != null && delta > 0 ? "text-status-success" : delta != null && delta < 0 ? "text-status-error" : "text-lia-text-tertiary"

  return (
    <div className="mt-2.5">
      <div className="flex items-center justify-between mb-1">
        <span className="text-[11px] text-lia-text-tertiary">Conversão triagem → entrevista</span>
        <div className="flex items-center gap-1">
          <span className="text-xs font-semibold text-lia-text-primary">{rate}%</span>
          {delta != null && delta !== 0 && (
            <span className={`flex items-center gap-0.5 text-[10px] font-medium ${deltaColor}`}>
              <DeltaIcon className="w-3 h-3" />
              {delta > 0 ? "+" : ""}{delta}%
            </span>
          )}
        </div>
      </div>
      <div className="w-full h-1.5 bg-lia-bg-secondary rounded-full overflow-hidden">
        <div className={`h-full ${barColor} rounded-full transition-all duration-500`} style={{ width: `${barWidth}%` }} />
      </div>
    </div>
  )
}

export function WeeklyDigestChatMessage({
  digest,
  recruiterName = "Ana",
}: WeeklyDigestChatMessageProps) {
  const [expanded, setExpanded] = useState<ExpandedSection>(null)

  const toggle = (section: ExpandedSection) => setExpanded(prev => prev === section ? null : section)

  const hasRiskJobs = digest.atRiskJobs.length > 0
  const criticalCount = digest.atRiskJobs.filter(j => j.severity === "critical").length
  const warningCount = digest.atRiskJobs.filter(j => j.severity === "warning").length

  return (
    <div className="space-y-2.5 max-w-[480px]">
      <div className="flex items-center gap-2 mb-1">
        <span className="bg-wedo-cyan/10 text-wedo-cyan-text text-[10px] font-semibold px-2 py-0.5 rounded-full border border-wedo-cyan/30">
          RESUMO SEMANAL
        </span>
        <span className="text-[10px] text-lia-text-tertiary">{digest.date}</span>
      </div>

      <p className="text-sm text-lia-text-secondary">
        Bom dia, {recruiterName}. Preparei o resumo da sua semana de recrutamento.
      </p>

      <div className="bg-lia-bg-secondary rounded-lg p-3.5 border border-lia-border-subtle">
        <p className="text-[10px] font-semibold text-lia-text-tertiary mb-3 uppercase tracking-wider">
          Pipeline da Semana
        </p>
        <div className="flex items-start justify-around">
          <KpiCell value={digest.pipeline.activeJobs} label="vagas ativas" color="text-wedo-cyan" />
          <div className="w-px h-10 bg-lia-border-subtle self-center" />
          <KpiCell value={digest.pipeline.screened} label="triados" color="text-status-success" />
          <div className="w-px h-10 bg-lia-border-subtle self-center" />
          <KpiCell value={digest.pipeline.interviews} label="entrevistas" color="text-lia-text-primary" />
        </div>

        {digest.pipeline.conversionRate != null && (
          <ConversionBar rate={digest.pipeline.conversionRate} delta={digest.pipeline.conversionDelta} />
        )}
      </div>

      {hasRiskJobs && (
        <div className="rounded-lg border border-status-warning/30 overflow-hidden">
          <button
            className="w-full flex items-center justify-between px-3.5 py-2.5 bg-status-warning/8 hover:bg-status-warning/12 transition-colors text-left"
            onClick={() => toggle("risk")}
            aria-expanded={expanded === "risk"}
            aria-controls="digest-risk-details"
          >
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-3.5 h-3.5 text-status-warning" />
              <span className="text-xs font-semibold text-status-warning">
                {digest.atRiskJobs.length} vaga{digest.atRiskJobs.length !== 1 ? "s" : ""} em risco
              </span>
              {criticalCount > 0 && (
                <span className="bg-status-error/15 text-status-error text-[9px] font-semibold px-1.5 py-0.5 rounded-full">
                  {criticalCount} crític{criticalCount !== 1 ? "as" : "a"}
                </span>
              )}
              {warningCount > 0 && (
                <span className="bg-status-warning/15 text-status-warning text-[9px] font-semibold px-1.5 py-0.5 rounded-full">
                  {warningCount} atenção
                </span>
              )}
            </div>
            {expanded === "risk"
              ? <ChevronUp className="w-3.5 h-3.5 text-status-warning" />
              : <ChevronDown className="w-3.5 h-3.5 text-status-warning" />}
          </button>

          {expanded === "risk" && (
            <div id="digest-risk-details" className="px-3.5 py-2.5 space-y-2 bg-lia-bg-primary border-t border-status-warning/20">
              {digest.atRiskJobs.map((job, i) => {
                const progress = job.targetDays > 0 ? Math.min((job.daysOpen / job.targetDays) * 100, 100) : 0
                const barColor = job.severity === "critical" ? "bg-status-error" : "bg-status-warning"

                return (
                  <div key={i} className="space-y-1">
                    <div className="flex items-center justify-between">
                      <p className="text-xs font-medium text-lia-text-primary truncate pr-2">
                        {job.title}
                        <span className="text-lia-text-tertiary font-normal"> — {job.company}</span>
                      </p>
                      <span className={`text-[9px] font-semibold px-1.5 py-0.5 rounded-full shrink-0 ${
                        job.severity === "critical"
                          ? "bg-status-error/15 text-status-error"
                          : "bg-status-warning/15 text-status-warning"
                      }`}>
                        {job.severity === "critical" ? "crítico" : "atenção"}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-1 bg-lia-bg-secondary rounded-full overflow-hidden">
                        <div className={`h-full ${barColor} rounded-full`} style={{ width: `${progress}%` }} />
                      </div>
                      <span className="text-[9px] text-lia-text-tertiary whitespace-nowrap">
                        {job.daysOpen}/{job.targetDays}d
                      </span>
                    </div>
                    {job.detail && (
                      <p className="text-[10px] text-lia-text-tertiary">{job.detail}</p>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}

      <div className="rounded-lg border border-status-success/30 overflow-hidden">
        <div className="flex items-start gap-2.5 px-3.5 py-2.5 bg-status-success/5">
          <Shield className="w-3.5 h-3.5 text-status-success mt-0.5 shrink-0" />
          <div>
            <p className="text-xs font-semibold text-status-success mb-0.5">Compliance e Fairness</p>
            <p className="text-[11px] text-lia-text-secondary leading-relaxed">{digest.compliance.message}</p>
          </div>
        </div>
      </div>

      {digest.optimization && (
        <div className="rounded-lg border border-wedo-cyan/30 overflow-hidden">
          <div className="flex items-start gap-2.5 px-3.5 py-2.5 bg-wedo-cyan/5">
            <Lightbulb className="w-3.5 h-3.5 text-wedo-cyan mt-0.5 shrink-0" />
            <div>
              <p className="text-xs font-semibold text-lia-text-secondary mb-0.5">Padrões e Otimização</p>
              <p className="text-[11px] text-lia-text-secondary leading-relaxed">{digest.optimization.message}</p>
            </div>
          </div>
        </div>
      )}

      <div className="rounded-lg border border-lia-border-subtle overflow-hidden">
        <button
          className="w-full flex items-center justify-between px-3.5 py-2.5 bg-lia-bg-secondary hover:bg-lia-interactive-active transition-colors text-left"
          onClick={() => toggle("metrics")}
          aria-expanded={expanded === "metrics"}
          aria-controls="digest-metrics-details"
        >
          <span className="text-xs font-medium text-lia-text-secondary">Métricas detalhadas</span>
          {expanded === "metrics"
            ? <ChevronUp className="w-3.5 h-3.5 text-lia-text-tertiary" />
            : <ChevronDown className="w-3.5 h-3.5 text-lia-text-tertiary" />}
        </button>
        {expanded === "metrics" && (
          <div id="digest-metrics-details" className="px-3.5 py-2.5 border-t border-lia-border-subtle bg-lia-bg-primary space-y-2">
            <div className="flex justify-between text-xs">
              <span className="text-lia-text-tertiary">Vagas ativas</span>
              <span className="text-lia-text-primary font-medium">{digest.pipeline.activeJobs}</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-lia-text-tertiary">Candidatos triados</span>
              <span className="text-lia-text-primary font-medium">{digest.pipeline.screened}</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-lia-text-tertiary">Entrevistas agendadas</span>
              <span className="text-lia-text-primary font-medium">{digest.pipeline.interviews}</span>
            </div>
            {digest.pipeline.conversionRate != null && (
              <div className="flex justify-between text-xs">
                <span className="text-lia-text-tertiary">Conversão triagem → entrevista</span>
                <div className="flex items-center gap-1">
                  <span className="text-lia-text-primary font-medium">{digest.pipeline.conversionRate}%</span>
                  {digest.pipeline.conversionDelta != null && digest.pipeline.conversionDelta !== 0 && (
                    <span className={`text-[10px] ${digest.pipeline.conversionDelta > 0 ? "text-status-success" : "text-status-error"}`}>
                      ({digest.pipeline.conversionDelta > 0 ? "+" : ""}{digest.pipeline.conversionDelta}%)
                    </span>
                  )}
                </div>
              </div>
            )}
            <div className="flex justify-between text-xs">
              <span className="text-lia-text-tertiary">Compliance</span>
              <span className={`font-medium ${
                digest.compliance.status === "ok" ? "text-status-success" : "text-status-warning"
              }`}>
                {digest.compliance.status === "ok" ? "OK" : "Atenção"}
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
