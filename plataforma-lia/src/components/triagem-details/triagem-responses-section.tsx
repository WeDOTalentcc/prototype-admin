"use client"

import {
  MessageSquare, CheckCircle, ChevronDown, ChevronUp, ShieldAlert, AlertTriangle, Star, Calculator, Info
} from "lucide-react"
import { cn } from "@/lib/utils"
import type { WSIResultDetails } from "@/services/lia-api"
import type { F11ReportData } from "./useTriagemDetailsState"
import {
  getFrameworkLabel, getScoreColor3Tier, bloomLabel, dreyfusLabel, gapConfig, starComponents
} from "./useTriagemDetailsState"

interface TriagemResponsesSectionProps {
  responses: WSIResultDetails["responses"]
  f11Report: F11ReportData | null
  expandedSections: Set<string>
  toggleSection: (section: string) => void
}

// Audit task #529 (G23-03 frontend) — Mapeamento de chaves técnicas para
// rótulos legíveis em PT-BR no breakdown "Como cheguei nesta nota".
const PENALTY_LABELS: Record<string, string> = {
  superficial: "Resposta superficial",
  incoherent: "Incoerência detectada",
  inconsistent: "Inconsistência entre respostas",
  red_flag: "Sinal de alerta (red flag)",
  red_flags: "Sinais de alerta (red flags)",
  contradiction: "Contradição",
  low_dreyfus: "Nível Dreyfus abaixo do esperado",
  low_bloom: "Nível Bloom abaixo do esperado",
  off_topic: "Resposta fora do tema",
  too_short: "Resposta muito curta",
  generic: "Resposta genérica",
  consistency_penalty: "Penalidade de consistência",
}

const BONUS_LABELS: Record<string, string> = {
  specificity: "Especificidade (exemplos concretos)",
  star_complete: "STAR completo (S+T+A+R)",
  high_dreyfus: "Nível Dreyfus acima do esperado",
  high_bloom: "Nível Bloom acima do esperado",
  measurable_result: "Resultado mensurável",
  evidence_rich: "Múltiplas evidências",
  consistency_bonus: "Bônus de consistência",
}

const humanizeKey = (key: string) =>
  key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())

const formatDelta = (value: number, sign: "+" | "-") => {
  const abs = Math.abs(value)
  return `${sign}${abs.toFixed(2)}`
}

export function TriagemResponsesSection({
  responses, f11Report, expandedSections, toggleSection
}: TriagemResponsesSectionProps) {
  const f11Analyses = f11Report?.response_analyses || []
  const f11Map: Record<string, { competency: string; score?: number; analysis?: string }> = {}
  f11Analyses.forEach((a: any) => { if (a.competency) f11Map[a.competency] = a as { competency: string; score?: number; analysis?: string } })

  return (
    <div className="border border-lia-border-subtle bg-lia-bg-secondary rounded-lg overflow-hidden">
      <div className={cn("cursor-pointer p-3 flex items-center justify-between hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none", expandedSections.has('responses') && "")} onClick={() => toggleSection('responses')}>
        <h3 className="text-xs font-semibold flex items-center gap-2 text-lia-text-primary">
          <MessageSquare className="w-4 h-4 text-lia-text-secondary" />
          Respostas por Competência ({responses.length})
        </h3>
        {expandedSections.has('responses') ? <ChevronUp className="w-4 h-4 text-lia-text-secondary" /> : <ChevronDown className="w-4 h-4 text-lia-text-secondary" />}
      </div>
      {expandedSections.has('responses') && (
        <div className="divide-y divide-lia-border-subtle">
          {responses.map((resp, idx) => {
            const f11 = (f11Map[resp.competency] || {}) as any
            const starData = f11.star || { S: false, T: false, A: false, R: false }
            const gapStatus = (f11.gap_status || 'ok') as keyof typeof gapConfig
            const gap = gapConfig[gapStatus] || gapConfig.ok
            const GapIcon = gap.icon
            const isCritical = f11.is_critical || (resp as any).question?.is_critical || false
            const bloomExpected = f11.bloom_expected || resp.scores.bloom_level || 3
            const bloomExpLabel = f11.bloom_expected_label || bloomLabel(bloomExpected)
            const dreyfusExpected = f11.dreyfus_expected || resp.scores.dreyfus_level || 3
            const dreyfusExpLabel = f11.dreyfus_expected_label || dreyfusLabel(dreyfusExpected)
            const demonstrated_bloom = f11.bloom_level || resp.scores.bloom_level || 3
            const demonstrated_dreyfus = f11.dreyfus_level || resp.scores.dreyfus_level || 3
            const finalScore = f11.final_score ?? resp.scores.final_score
            const isOpen = expandedSections.has(`resp-${idx}`)
            return (
              <div key={`resp-${idx}`}>
                <button
                  className="w-full flex items-center justify-between px-4 py-3 hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none text-left"
                  onClick={() => toggleSection(`resp-${idx}`)}
                >
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm font-medium text-lia-text-primary">{resp.competency}</span>
                    <span className="text-micro bg-lia-bg-tertiary text-lia-text-secondary px-2 py-0.5 rounded-full">{getFrameworkLabel(resp.question?.framework || f11.framework || '')}</span>
                    {isCritical && (
                      <span className="flex items-center gap-0.5 text-micro font-bold text-status-error bg-status-error/10 border border-status-error/30 px-1.5 py-0.5 rounded-full">
                        <ShieldAlert className="w-2.5 h-2.5" /> Crítica
                      </span>
                    )}
                    {/* Audit task #529 (G23-02 frontend) — sinaliza resposta sem Camada 2. */}
                    {resp.degraded_quality && (
                      <span
                        className="flex items-center gap-0.5 text-micro font-semibold text-status-warning bg-status-warning/10 border border-status-warning/30 px-1.5 py-0.5 rounded-full"
                        title={resp.layer2_degraded_reason || "Análise semântica indisponível"}
                      >
                        <AlertTriangle className="w-2.5 h-2.5" /> Sem Camada 2
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`text-sm font-bold ${getScoreColor3Tier(finalScore)}`}>
                      {finalScore.toFixed(1)}/10.0
                    </span>
                    {isOpen ? <ChevronUp className="w-4 h-4 text-lia-text-secondary" /> : <ChevronDown className="w-4 h-4 text-lia-text-secondary" />}
                  </div>
                </button>

                {isOpen && (
                  <div className="px-4 pb-4 space-y-4 bg-lia-bg-secondary/50">
                    <div className="space-y-2">
                      <div className="bg-lia-bg-primary border border-lia-border-subtle rounded-lg p-3">
                        <p className="text-micro text-lia-text-secondary uppercase tracking-wide mb-1">Pergunta</p>
                        <p className="text-xs text-lia-text-secondary leading-relaxed">{resp.question?.text || f11.question_text}</p>
                      </div>
                      <div className="bg-lia-bg-primary border border-lia-border-subtle rounded-lg p-3">
                        <p className="text-micro text-lia-text-secondary uppercase tracking-wide mb-1" aria-live="polite" aria-atomic="true">Resposta do Candidato</p>
                        <p className="text-xs text-lia-text-primary leading-relaxed">{resp.response_text}</p>
                      </div>
                    </div>

                    <div className="bg-lia-bg-primary border border-lia-border-subtle rounded-lg p-3">
                      <p className="text-micro text-lia-text-secondary uppercase tracking-wide mb-2">Qualidade da resposta (STAR)</p>
                      <div className="flex items-center gap-2 flex-wrap">
                        {starComponents.map(({ key, label, desc }) => {
                          const present = starData[key]
                          return (
                            <div
                              key={key}
                              title={desc}
                              className={`flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold border ${
present
                                  ? "bg-status-success/10 border-status-success/30 text-status-success"
                                  : "bg-lia-bg-tertiary border-lia-border-subtle text-lia-text-secondary"
                              }`}
                            >
                              {present
                                ? <CheckCircle className="w-3 h-3" />
                                : <span className="w-3 h-3 flex items-center justify-center text-lia-text-tertiary font-bold text-micro">–</span>
                              }
                              <span>{label}</span>
                            </div>
                          )
                        })}
                        {!starData.R && (
                          <span className="text-micro text-status-warning bg-status-warning/10 border border-status-warning/20 px-2 py-0.5 rounded-full" aria-live="polite" aria-atomic="true">
                            Resultado não evidenciado
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="grid grid-cols-4 gap-2">
                      {[
                        { label: "Autodeclaração", value: (f11.autodeclaration_score ?? resp.scores.autodeclaration)?.toFixed(1) },
                        { label: "Contexto", value: (f11.context_score ?? resp.scores.context)?.toFixed(1) },
                        { label: "Bloom", value: bloomLabel(demonstrated_bloom), sub: `Nível ${demonstrated_bloom}` },
                        { label: "Dreyfus", value: dreyfusLabel(demonstrated_dreyfus), sub: `Nível ${demonstrated_dreyfus}` },
                      ].map((s) => (
                        <div key={s.label} className="bg-lia-bg-primary border border-lia-border-subtle rounded-lg p-2 text-center">
                          <p className="text-micro text-lia-text-secondary mb-1">{s.label}</p>
                          <p className="text-sm font-bold text-lia-text-primary">{s.value}</p>
                        </div>
                      ))}
                    </div>

                    <div className={`flex items-center justify-between rounded-lg border px-3 py-2.5 ${gap.bg} ${gap.border}`}>
                      <div className="flex items-center gap-2">
                        <GapIcon className={`w-3.5 h-3.5 ${gap.color}`} />
                        <span className={`text-xs font-medium ${gap.color}`} aria-live="polite" aria-atomic="true">Esperado pela vaga</span>
                      </div>
                      <div className="flex items-center gap-4 text-xs">
                        <div className="text-right">
                          <p className="text-micro text-lia-text-secondary">Bloom</p>
                          <p className={`font-semibold ${gap.color}`}>{bloomLabel(bloomExpected)}</p>
                        </div>
                        <div className="text-right">
                          <p className="text-micro text-lia-text-secondary">Dreyfus</p>
                          <p className={`font-semibold ${gap.color}`}>{dreyfusLabel(dreyfusExpected)}</p>
                        </div>
                        <span className={`text-micro font-medium px-2 py-0.5 rounded-full ${gap.bg} ${gap.color} border ${gap.border}`}>
                          {gap.label}
                        </span>
                      </div>
                    </div>

                    {resp.evidences && resp.evidences.length > 0 && (
                      <div>
                        <p className="text-micro text-lia-text-secondary uppercase tracking-wide mb-2">Evidências</p>
                        <div className="flex flex-wrap gap-2">
                          {resp.evidences.map((ev, i) => (
                            <span key={`ev-${i}`} className="flex items-center gap-1 text-xs bg-lia-bg-primary border border-lia-border-subtle text-lia-text-secondary px-2 py-1 rounded-full">
                              <CheckCircle className="w-3 h-3 text-status-success" /> {ev}
                            </span>
                          ))}
                        </div>
                        <p className="text-xs text-lia-text-secondary italic mt-2">{resp.justification || f11.justification}</p>
                      </div>
                    )}

                    {/* Audit task #529 (G23-03 frontend) — "Como cheguei nesta nota":
                        breakdown granular de penalidades/bônus para LGPD Art. 20.
                        Só é renderizado quando há ao menos um ajuste (penalidade
                        ou bônus) — respostas sem ajustes não exibem o bloco. */}
                    {(() => {
                      const penalties = Object.entries(resp.penalty_breakdown || {}).filter(([, v]) => Number(v) > 0)
                      const bonuses = Object.entries(resp.bonus_breakdown || {}).filter(([, v]) => Number(v) > 0)
                      if (penalties.length === 0 && bonuses.length === 0) return null
                      const totalPenalty = penalties.reduce((acc, [, v]) => acc + Number(v), 0)
                      const totalBonus = bonuses.reduce((acc, [, v]) => acc + Number(v), 0)
                      const baseScore = finalScore + totalPenalty - totalBonus
                      const breakdownKey = `breakdown-${idx}`
                      const isBreakdownOpen = expandedSections.has(breakdownKey)
                      return (
                        <div className="border border-lia-border-subtle rounded-lg overflow-hidden">
                          <button
                            type="button"
                            className="w-full flex items-center justify-between px-3 py-2 bg-lia-bg-primary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none text-left"
                            onClick={() => toggleSection(breakdownKey)}
                            aria-expanded={isBreakdownOpen}
                          >
                            <span className="flex items-center gap-2 text-xs font-medium text-lia-text-primary">
                              <Calculator className="w-3.5 h-3.5 text-lia-text-secondary" />
                              Como cheguei nesta nota
                            </span>
                            {isBreakdownOpen
                              ? <ChevronUp className="w-3.5 h-3.5 text-lia-text-secondary" />
                              : <ChevronDown className="w-3.5 h-3.5 text-lia-text-secondary" />}
                          </button>
                          {isBreakdownOpen && (
                            <div className="px-3 py-3 bg-lia-bg-primary border-t border-lia-border-subtle space-y-2">
                              <div className="flex items-center justify-between text-xs">
                                <span className="text-lia-text-secondary">Score base</span>
                                <span className="font-medium text-lia-text-primary">{baseScore.toFixed(2)}</span>
                              </div>

                              {penalties.length > 0 && (
                                <div className="space-y-1">
                                  <p className="text-micro text-lia-text-secondary uppercase tracking-wide">Penalidades aplicadas</p>
                                  {penalties.map(([key, value]) => (
                                    <div key={`pen-${key}`} className="flex items-center justify-between text-xs">
                                      <span className="text-lia-text-primary">{PENALTY_LABELS[key] || humanizeKey(key)}</span>
                                      <span className="font-mono font-medium text-status-error">{formatDelta(Number(value), "-")}</span>
                                    </div>
                                  ))}
                                </div>
                              )}

                              {bonuses.length > 0 && (
                                <div className="space-y-1">
                                  <p className="text-micro text-lia-text-secondary uppercase tracking-wide">Bônus aplicados</p>
                                  {bonuses.map(([key, value]) => (
                                    <div key={`bon-${key}`} className="flex items-center justify-between text-xs">
                                      <span className="text-lia-text-primary">{BONUS_LABELS[key] || humanizeKey(key)}</span>
                                      <span className="font-mono font-medium text-status-success">{formatDelta(Number(value), "+")}</span>
                                    </div>
                                  ))}
                                </div>
                              )}

                              <div className="flex items-center justify-between text-xs pt-2 border-t border-lia-border-subtle">
                                <span className="font-semibold text-lia-text-primary">Score final</span>
                                <span className={`font-bold ${getScoreColor3Tier(finalScore)}`}>{finalScore.toFixed(2)}</span>
                              </div>

                              {resp.degraded_quality && (
                                <div className="flex items-start gap-1.5 pt-2 border-t border-lia-border-subtle text-micro text-lia-text-secondary">
                                  <Info className="w-3 h-3 mt-0.5 shrink-0 text-status-warning" />
                                  <span>
                                    Análise semântica (Camada 2) não disponível para esta resposta.
                                    Pontuação calculada por regras determinísticas.
                                    {resp.layer2_degraded_reason ? ` Motivo: ${resp.layer2_degraded_reason}.` : ""}
                                  </span>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      )
                    })()}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
