"use client"

import type { WeeklyDigestData } from "./weekly-digest-notification"

interface WeeklyDigestChatMessageProps {
  digest: WeeklyDigestData
  recruiterName?: string
  onDetailRiskJobs?: () => void
  onViewMetrics?: () => void
}

export function WeeklyDigestChatMessage({
  digest,
  recruiterName = "Ana",
  onDetailRiskJobs,
  onViewMetrics,
}: WeeklyDigestChatMessageProps) {
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 mb-1">
        <span className="bg-wedo-cyan/10 text-wedo-cyan text-[10px] font-semibold px-2 py-0.5 rounded-full border border-wedo-cyan/30">
          RESUMO SEMANAL
        </span>
        <span className="text-[10px] text-lia-text-tertiary">{digest.date}</span>
      </div>

      <p className="text-sm text-lia-text-secondary">
        Bom dia, {recruiterName}. Preparei o resumo da sua semana de recrutamento.
      </p>

      <div className="bg-lia-bg-secondary rounded-lg p-3 border border-lia-border-subtle">
        <p className="text-xs font-semibold text-lia-text-tertiary mb-2 uppercase tracking-wide">Pipeline</p>
        <div className="flex items-center gap-4">
          <div className="text-center">
            <p className="text-xl font-semibold text-wedo-cyan">{digest.pipeline.activeJobs}</p>
            <p className="text-[10px] text-lia-text-tertiary">vagas</p>
          </div>
          <div className="text-center">
            <p className="text-xl font-semibold text-status-success">{digest.pipeline.screened}</p>
            <p className="text-[10px] text-lia-text-tertiary">triados</p>
          </div>
          <div className="text-center">
            <p className="text-xl font-semibold text-status-warning">{digest.pipeline.interviews}</p>
            <p className="text-[10px] text-lia-text-tertiary">entrevistas</p>
          </div>
        </div>
        {digest.pipeline.conversionRate != null && (
          <p className="text-xs text-lia-text-tertiary mt-2">
            Conversão triagem→entrevista: {digest.pipeline.conversionRate}%
            {digest.pipeline.conversionDelta != null && digest.pipeline.conversionDelta > 0 && (
              <span className="text-status-success"> (+{digest.pipeline.conversionDelta}%)</span>
            )}
          </p>
        )}
      </div>

      {digest.atRiskJobs.length > 0 && (
        <div className="bg-status-warning/10 rounded-lg p-3 border border-status-warning/30">
          <p className="text-xs font-semibold text-status-warning mb-1.5">
            {digest.atRiskJobs.length} vaga{digest.atRiskJobs.length !== 1 ? "s" : ""} precisa{digest.atRiskJobs.length !== 1 ? "m" : ""} de atenção
          </p>
          <ul className="space-y-1.5">
            {digest.atRiskJobs.map((job, i) => (
              <li key={i} className="flex items-start gap-1.5">
                <span className={`w-1.5 h-1.5 rounded-full mt-1.5 shrink-0 ${
                  job.severity === "critical" ? "bg-status-error" : "bg-status-warning"
                }`} />
                <p className="text-xs text-lia-text-secondary">
                  <span className="font-medium">{job.title} — {job.company}:</span>{" "}
                  {job.detail || `${job.daysOpen} dias abertos (meta: ${job.targetDays}).`}
                </p>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="bg-status-success/10 rounded-lg p-3 border border-status-success/30">
        <p className="text-xs font-semibold text-status-success mb-1">Compliance e Fairness</p>
        <p className="text-xs text-lia-text-secondary">{digest.compliance.message}</p>
      </div>

      {digest.optimization && (
        <div className="bg-wedo-cyan/10 rounded-lg p-3 border border-wedo-cyan/30">
          <p className="text-xs font-semibold text-wedo-cyan mb-1">Padrões e Otimização</p>
          <p className="text-xs text-lia-text-secondary">{digest.optimization.message}</p>
        </div>
      )}

      {(onDetailRiskJobs || onViewMetrics) && (
        <div className="flex gap-2 mt-2">
          {onDetailRiskJobs && (
            <button
              className="text-xs bg-wedo-cyan/10 text-wedo-cyan px-3 py-1.5 rounded-lg border border-wedo-cyan/30 hover:bg-wedo-cyan/20 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-wedo-cyan/50 focus-visible:ring-offset-1"
              onClick={onDetailRiskJobs}
              aria-label="Detalhar vagas em risco — navegar para página de Vagas"
            >
              Detalhar vagas em risco
            </button>
          )}
          {onViewMetrics && (
            <button
              className="text-xs bg-lia-bg-secondary text-lia-text-secondary px-3 py-1.5 rounded-lg border border-lia-border-subtle hover:bg-lia-bg-primary transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gray-400/50 focus-visible:ring-offset-1"
              onClick={onViewMetrics}
              aria-label="Ver métricas completas — navegar para Visão do Pipeline"
            >
              Ver métricas completas
            </button>
          )}
        </div>
      )}
    </div>
  )
}
