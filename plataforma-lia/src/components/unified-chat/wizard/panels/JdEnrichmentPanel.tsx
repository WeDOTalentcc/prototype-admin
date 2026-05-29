"use client"

import React, { useState, useEffect } from"react"
import { cn } from"@/lib/utils"
import { CheckCircle, AlertTriangle, XCircle, Brain, Shield } from"lucide-react"
import type { JdEnrichmentData } from"../wizard-types"
import { FallbackBanner } from "./FallbackBanner"
import { AiDegradedModeBanner } from "./AiDegradedModeBanner"

interface Props {
  data: Record<string, unknown>
  requiresApproval: boolean
  onApprove?: () => void
  onReject?: () => void
}

function getQualityBadge(score: number) {
  if (score >= 70) return { label:"Bom", icon: CheckCircle, color:"text-status-success bg-status-success/10" }
  if (score >= 50) return { label:"Adequado", icon: CheckCircle, color:"text-wedo-cyan bg-wedo-cyan/10" }
  if (score >= 30) return { label:"Insuficiente", icon: AlertTriangle, color:"text-status-warning bg-status-warning/10" }
  return { label:"Critico", icon: XCircle, color:"text-status-error bg-status-error/10" }
}

/**
 * JdEnrichmentPanel — F1 HITL approval panel.
 * Shows enriched JD vs original, quality score badge, fairness corrections.
 * Recruiter approves or rejects.
 */
export function JdEnrichmentPanel({ data, requiresApproval, onApprove, onReject }: Props) {
  const d = data as unknown as JdEnrichmentData
  const enriched = d.jd_enriched
  const score = d.quality_score || 0
  const warnings = d.quality_warnings || []
  const badge = getQualityBadge(score)
  const BadgeIcon = badge.icon

  // Canonical idle state — backend signals "awaiting JD content from recruiter".
  // Source: lia-agent-system/app/domains/job_creation/nodes/jd_enrichment.py:269
  // emits {awaiting_jd_input: true, message: ...} when raw_input is too thin.
  // Without this branch, panel would render misleading "Critico 0/100" + 30s timeout.
  if (d.awaiting_jd_input) {
    return <JdAwaitingInputState message={d.message} />
  }

  return (
    <div className="flex flex-col">
      {/* Task #1070 — banner de modo degradado agregado (sessao/tenant). */}
      <AiDegradedModeBanner state={d.ai_degraded_mode ?? null} />
      {/* Task #1065/#1067 — banner de fallback determinístico com root-cause. */}
      {d.jd_enrichment_used_fallback && (
        <FallbackBanner
          reason={d.jd_enrichment_fallback_reason ?? undefined}
          onRetry={() =>
            window.dispatchEvent(
              new CustomEvent("lia:wizard-retry-stage", {
                detail: { stage: "jd_enrichment" },
              }),
            )
          }
        />
      )}
      {/* Quality score badge — only when enrichment actually completed (score real, not default-0). */}
      {enriched && (
        <div className="px-4 py-3">
          <div className="flex items-center gap-2">
            <div className={cn("flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium", badge.color)}>
              <BadgeIcon className="w-3.5 h-3.5" />
              <span >{badge.label}</span>
            </div>
            <span className="text-xs text-lia-text-secondary">
              Score: {score}/100
            </span>
          </div>
          {warnings.length > 0 && (
            <div className="mt-2 space-y-1">
              {warnings.map((w, i) => (
                <p key={i} className="text-xs text-status-warning flex items-start gap-1">
                  <AlertTriangle className="w-3 h-3 mt-0.5 flex-shrink-0" />
                  {w}
                </p>
              ))}
            </div>
          )}
        </div>
      )}

      {enriched ? (
        <div className="px-4 py-3 space-y-4">
          {/* Title + Seniority */}
          <div>
            <h4 className="text-sm font-semibold text-lia-text-primary">
              {enriched.titulo_padronizado}
            </h4>
            <p className="text-xs text-lia-text-secondary mt-0.5">
              {enriched.senioridade_confirmada}
            </p>
          </div>

          {/* About */}
          {enriched.about_role && (
            <div>
              <p className="text-xs font-medium text-lia-text-secondary mb-1">Sobre o cargo</p>
              <p className="text-sm text-lia-text-primary leading-relaxed">
                {enriched.about_role}
              </p>
            </div>
          )}

          {/* Skills obrigatorias */}
          {enriched.skills_obrigatorias?.length > 0 && (
            <div>
              <p className="text-xs font-medium text-lia-text-secondary mb-1.5">
                Skills obrigatorias ({enriched.skills_obrigatorias.length})
              </p>
              <div className="flex flex-wrap gap-1.5">
                {enriched.skills_obrigatorias.map((s, i) => (
                  <span
                    key={i}
                    className="inline-flex items-center px-2 py-0.5 rounded bg-lia-bg-secondary border border-lia-border-subtle text-xs text-lia-text-primary"
                  >
                    {s.skill}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Competencias comportamentais */}
          {enriched.competencias_comportamentais?.length > 0 && (
            <div>
              <p className="text-xs font-medium text-lia-text-secondary mb-1.5">
                Competencias comportamentais ({enriched.competencias_comportamentais.length})
              </p>
              <div className="space-y-1.5">
                {enriched.competencias_comportamentais.map((c, i) => (
                  <div key={i} className="flex items-center gap-2 text-xs">
                    <span className="text-lia-text-primary">{c.competencia}</span>
                    <span className="px-1.5 py-0.5 rounded  text-[10px] font-medium">
                      {c.trait_big_five}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Fairness corrections */}
          {enriched.fairness_corrections?.length > 0 && (
            <div className="p-2.5 rounded-md bg-status-success/5 border border-status-success/20">
              <div className="flex items-center gap-1.5 mb-1">
                <Shield className="w-3.5 h-3.5 text-status-success" />
                <span className="text-xs font-medium text-status-success">
                  Correcoes de fairness aplicadas
                </span>
              </div>
              {enriched.fairness_corrections.map((c, i) => (
                <p key={i} className="text-xs text-lia-text-secondary ml-5">
                  {c}
                </p>
              ))}
            </div>
          )}

          {/* Alteracoes */}
          {enriched.alteracoes_realizadas?.length > 0 && (
            <div>
              <div className="flex items-center gap-1.5 mb-1">
                <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
                <span className="text-xs font-medium text-lia-text-secondary">
                  Alteracoes realizadas pela IA
                </span>
              </div>
              <ul className="space-y-0.5 ml-5">
                {enriched.alteracoes_realizadas.map((a, i) => (
                  <li key={i} className="text-xs text-lia-text-secondary">
                    {a}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      ) : (
        <JdLoadingState key={String(d.quality_score)} />
      )}

      {/* HITL Approval footer — only when enriched and approval needed */}
      {requiresApproval && enriched && (
        <div className="flex-shrink-0 px-4 py-3 border-t border-lia-border-subtle bg-lia-bg-primary flex items-center gap-2">
          <button
            onClick={onReject}
            className="flex-1 px-3 py-2 rounded-md border border-lia-border-subtle text-sm font-medium text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
          >
            Editar
          </button>
          <button
            onClick={onApprove}
            className="flex-1 px-3 py-2 rounded-md bg-wedo-cyan text-white text-sm font-medium hover:bg-wedo-cyan/90 transition-colors motion-reduce:transition-none"
          >
            Aprovar JD
          </button>
        </div>
      )}
    </div>
  )
}

function JdAwaitingInputState({ message }: { message?: string }) {
  return (
    <div
      data-testid="jd-awaiting-input"
      className="px-4 py-8 text-center space-y-3"
    >
      <div className="mx-auto w-10 h-10 rounded-full bg-wedo-cyan/10 flex items-center justify-center">
        <Brain className="w-5 h-5 text-wedo-cyan" aria-hidden="true" />
      </div>
      <p className="text-sm text-lia-text-primary font-medium">
        Aguardando descricao da vaga
      </p>
      <p className="text-xs text-lia-text-secondary leading-relaxed">
        {message ?? "Cole a descricao da vaga (JD) no chat — texto, PDF, DOCX ou TXT. A LIA enriquece automaticamente assim que receber."}
      </p>
    </div>
  )
}

function JdLoadingState() {
  const [timedOut, setTimedOut] = useState(false)

  useEffect(() => {
    const timer = setTimeout(() => setTimedOut(true), 30000)
    return () => clearTimeout(timer)
  }, [])

  if (timedOut) {
    return (
      <div className="px-4 py-8 text-center space-y-3">
        <p className="text-sm text-status-warning font-medium">
          O enriquecimento esta demorando mais que o esperado.
        </p>
        <p className="text-xs text-lia-text-tertiary">
          Verifique a conexao ou tente novamente no chat.
        </p>
        <button
          onClick={() => setTimedOut(false)}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-lia-border-subtle text-xs font-medium text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors"
        >
          Aguardar mais
        </button>
      </div>
    )
  }

  return (
    <div className="px-4 py-8 text-center space-y-2">
      <div className="w-5 h-5 mx-auto border-2 border-wedo-cyan border-t-transparent rounded-full animate-spin" />
      <p className="text-sm text-lia-text-secondary">
        Enriquecendo JD...
      </p>
    </div>
  )
}
