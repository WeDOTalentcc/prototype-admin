"use client"

import React, { useState, useEffect } from"react"
import { cn } from"@/lib/utils"
import { CheckCircle, AlertTriangle, XCircle, Brain, Shield, ChevronDown } from"lucide-react"
import type { JdEnrichmentData } from"../wizard-types"
import { FallbackBanner } from "./FallbackBanner"
import { AiDegradedModeBanner } from "./AiDegradedModeBanner"

const DIMENSION_INFO: Record<string, { definition: string; howToImprove: string }> = {
  D1: {
    definition: "Avalia se o título da vaga é claro, usa nomenclatura de mercado e inclui nível de senioridade.",
    howToImprove: "Inclua o nível (Júnior/Pleno/Sênior/Especialista) e use títulos reconhecidos no mercado.",
  },
  D2: {
    definition: "Verifica se a vaga lista responsabilidades concretas e específicas (mínimo 5).",
    howToImprove: "Adicione mais responsabilidades. Use verbos de ação: 'Liderar', 'Desenvolver', 'Implementar'.",
  },
  D3: {
    definition: "Mede a presença de skills técnicas mensuráveis (ferramentas, linguagens, plataformas).",
    howToImprove: "Liste ferramentas e tecnologias específicas que o candidato precisa dominar.",
  },
  D4: {
    definition: "Avalia se a vaga define competências comportamentais relevantes ao cargo.",
    howToImprove: "Adicione 3+ competências como 'Liderança', 'Comunicação', 'Visão estratégica'.",
  },
  D5: {
    definition: "Verifica se os requisitos, responsabilidades e salário são coerentes com o nível de senioridade.",
    howToImprove: "Revise os requisitos para alinhá-los ao nível declarado. Júnior e Sênior têm expectativas bem diferentes.",
  },
  D6: {
    definition: "Detecta contradições, repetições e linguagem excludente que prejudicam a qualidade.",
    howToImprove: "Revise a vaga para remover requisitos contraditórios e termos que possam afastar candidatos qualificados.",
  },
  D7: {
    definition: "Avalia se a vaga apresenta contexto sobre a empresa, equipe ou missão do cargo.",
    howToImprove: "Adicione informações sobre a empresa, tamanho da equipe, cultura ou impacto do cargo.",
  },
  D8: {
    definition: "Verifica o uso de linguagem neutra e inclusiva, sem termos que excluam grupos.",
    howToImprove: "Use 'você' em vez de termos generificados. Evite 'ninja', 'rockstar', 'nativo digital'.",
  },
  D9: {
    definition: "Mede a densidade do texto — vagas muito curtas não geram triagens precisas (mínimo 150 palavras).",
    howToImprove: "Expanda a descrição. Mais contexto e detalhes resultam em triagens mais precisas pela LIA.",
  },
}

function getDimensionAnalysis(ind: {
  dimension: string
  earned: number
  weight: number
  status: string
  count?: number
  minimum?: number
  word_count?: number
}): string {
  const pct = ind.weight > 0 ? ind.earned / ind.weight : 0

  if (ind.dimension === "D2" && ind.count !== undefined) {
    if (ind.count >= (ind.minimum ?? 5)) return `Ótimo! ${ind.count} responsabilidades listadas.`
    return `Apenas ${ind.count} responsabilidades. Mínimo recomendado: ${ind.minimum ?? 5}.`
  }
  if (ind.dimension === "D3" && ind.count !== undefined) {
    if (ind.count >= (ind.minimum ?? 3)) return `${ind.count} skills técnicas identificadas. Bom nível de especificidade.`
    return `Apenas ${ind.count} skills técnicas. Adicione mais ferramentas e tecnologias específicas.`
  }
  if (ind.dimension === "D4" && ind.count !== undefined) {
    if (ind.count >= 3) return `${ind.count} competências comportamentais definidas.`
    return `Apenas ${ind.count} competências comportamentais. Inclua pelo menos 3.`
  }
  if (ind.dimension === "D9" && ind.word_count !== undefined) {
    if (ind.word_count >= 150) return `${ind.word_count} palavras — boa densidade para triagem precisa.`
    return `Apenas ${ind.word_count} palavras. Expanda para pelo menos 150 para triagens de maior qualidade.`
  }

  if (pct >= 1) return "Dimensão completa. Nenhuma ação necessária."
  if (pct >= 0.7) return "Bom, com pequenas oportunidades de melhoria."
  if (pct >= 0.4) return "Dimensão parcialmente atendida. Melhora recomendada."
  return "Dimensão com lacunas significativas. Ação recomendada."
}


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
  const indicators = d.quality_indicators || []
  const [expandedDim, setExpandedDim] = React.useState<string | null>(null)
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
          {indicators.length > 0 && (
            <div className="mt-2">
              <p className="text-xs text-lia-text-secondary mb-1.5">
                {indicators.length} dimensões de qualidade
              </p>
              <div className="space-y-0.5">
                {indicators.map((ind) => {
                  const dot =
                    ind.status === "sufficient"
                      ? "bg-status-success"
                      : ind.status === "partial"
                      ? "bg-status-warning"
                      : "bg-lia-text-disabled"
                  const isOpen = expandedDim === ind.dimension
                  const info = DIMENSION_INFO[ind.dimension]

                  return (
                    <div key={ind.dimension}>
                      <button
                        type="button"
                        onClick={() => setExpandedDim(isOpen ? null : ind.dimension)}
                        className="w-full flex items-center gap-2 text-[11px] py-0.5 hover:bg-lia-interactive-hover rounded px-1 -mx-1 transition-colors text-left"
                        aria-expanded={isOpen}
                      >
                        <span className={cn("w-1.5 h-1.5 rounded-full flex-shrink-0", dot)} />
                        <span className="text-lia-text-secondary flex-1 min-w-0 truncate">
                          {ind.label}
                        </span>
                        <span className="text-lia-text-tertiary tabular-nums flex-shrink-0">
                          {ind.earned}/{ind.weight}
                        </span>
                        <ChevronDown className={cn(
                          "w-3 h-3 text-lia-text-disabled flex-shrink-0 transition-transform",
                          isOpen && "rotate-180"
                        )} />
                      </button>
                      {isOpen && info && (
                        <div className="mt-1 mb-2 ml-3.5 p-2.5 rounded-md bg-lia-bg-secondary border border-lia-border-subtle space-y-1.5">
                          <p className="text-[11px] text-lia-text-secondary leading-relaxed">
                            {info.definition}
                          </p>
                          <p className={cn(
                            "text-[11px] font-medium leading-relaxed",
                            ind.status === "sufficient" ? "text-status-success" : "text-status-warning"
                          )}>
                            {getDimensionAnalysis(ind)}
                          </p>
                          {ind.status !== "sufficient" && (
                            <p className="text-[11px] text-lia-text-tertiary leading-relaxed border-t border-lia-border-subtle pt-1.5">
                              💡 {info.howToImprove}
                            </p>
                          )}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
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
          {enriched.about_company && (
            <div>
              <p className="text-xs font-medium text-lia-text-secondary mb-1">Sobre a empresa</p>
              <p className="text-sm text-lia-text-primary leading-relaxed">
                {enriched.about_company}
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
