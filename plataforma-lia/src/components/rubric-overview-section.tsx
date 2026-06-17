"use client"

import React from "react"
import { Brain, CheckCircle, ArrowRight, Clock, Lightbulb } from "lucide-react"
import { getScoreColor } from "@/hooks/ai/use-rubric-evaluation"
import type { ParecerLIA, DecisionBadge, ScoreBadge, RubricEvaluationData } from "./rubric-evaluation-types"

interface RubricOverviewSectionProps {
  score: number
  scoreBadge: ScoreBadge
  decisionBadge: DecisionBadge | null
  evaluation: RubricEvaluationData
  essentialMet: number
  essentialReqsLength: number
  importantMet: number
  importantReqsLength: number
  desirableMet: number
  desirableReqsLength: number
  mockParecer: ParecerLIA
  mockWhyCandidate: string[]
}

export function RubricOverviewSection({
  score,
  scoreBadge,
  decisionBadge,
  evaluation,
  essentialMet,
  essentialReqsLength,
  importantMet,
  importantReqsLength,
  desirableMet,
  desirableReqsLength,
  mockParecer,
  mockWhyCandidate,
}: RubricOverviewSectionProps) {
  return (
    <div className="space-y-3" data-testid="rubric-overview-section">
      <div className="p-3 border border-lia-border-subtle rounded-lg bg-lia-bg-secondary">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-semibold text-lia-text-primary">Score de Aderência</span>
          <div className="flex items-center gap-2">
            <span
              className="text-micro font-medium px-2 py-0.5 rounded-full"
              style={{backgroundColor: scoreBadge.bg, color: scoreBadge.color}}
            >
              {evaluation.score_label || scoreBadge.label}
            </span>
            {decisionBadge && (
              <span
                className="text-micro font-medium px-2 py-0.5 rounded-full flex items-center gap-1"
                style={{backgroundColor: decisionBadge.bg, color: decisionBadge.color}}
              >
                <decisionBadge.icon className="w-3 h-3" />
                {decisionBadge.label}
              </span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex-1 h-3 rounded-full overflow-hidden bg-lia-bg-tertiary">
            <div
              className="h-full rounded-full transition-[width,height] duration-700 ease-out"
              style={{width: `${score}%`, backgroundColor: getScoreColor(score)}}
            />
          </div>
          <span className="text-xl font-semibold min-w-[55px] text-right text-lia-text-primary">
            {score}%
          </span>
        </div>

        <div className="grid grid-cols-3 gap-2 mt-3 pt-3 border-t border-t-lia-border-subtle">
          <div className="text-center">
            <div className="text-micro mb-1 text-lia-text-secondary">Essenciais</div>
            <div className={`text-base-ui font-semibold ${essentialMet === essentialReqsLength ? 'text-lia-btn-primary-bg' : 'text-status-warning'}`}>
              {essentialMet}/{essentialReqsLength}
            </div>
          </div>
          <div className="text-center border-l border-l-lia-border-subtle border-r border-r-lia-border-subtle">
            <div className="text-micro mb-1 text-lia-text-secondary">Importantes</div>
            <div className="text-base-ui font-semibold">
              {importantMet}/{importantReqsLength}
            </div>
          </div>
          <div className="text-center">
            <div className="text-micro mb-1 text-lia-text-secondary">Desejáveis</div>
            <div className="text-base-ui font-semibold">
              {desirableMet}/{desirableReqsLength}
            </div>
          </div>
        </div>
      </div>

      <div className="p-3 border border-lia-border-subtle rounded-lg bg-lia-bg-secondary">
        <h3 className="text-xs font-semibold flex items-center gap-2 mb-3 text-lia-text-primary">
          <Brain className="w-4 h-4 text-wedo-cyan" />
          Parecer de IA
        </h3>

        <div className="mb-3">
          <div className="text-micro font-semibold mb-1.5 flex items-center gap-1 text-lia-text-secondary">
            <span className="w-4 h-4 rounded-full flex items-center justify-center text-micro font-bold bg-wedo-cyan/[.12]">1</span>
            Contexto e Fit
          </div>
          <p className="text-xs leading-relaxed pl-5 text-lia-text-primary">
            {mockParecer.contexto_fit}
          </p>
        </div>

        {mockParecer.pontos_fortes_impacto && mockParecer.pontos_fortes_impacto.length > 0 && (
          <div className="mb-3">
            <div className="text-micro font-semibold mb-1.5 flex items-center gap-1 text-lia-text-secondary">
              <span className="w-4 h-4 rounded-full flex items-center justify-center text-micro font-bold bg-wedo-cyan/[.12]">2</span>
              Pontos Fortes e Impacto
            </div>
            <div className="space-y-1.5 pl-5">
              {mockParecer.pontos_fortes_impacto.map((pf, idx) => (
                <div key={`pf-${idx}`} className="p-2 rounded-xl bg-lia-bg-secondary">
                  <div className="flex items-start gap-2">
                    <CheckCircle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-lia-text-secondary" />
                    <div>
                      <span className="text-xs font-medium text-lia-text-primary">{pf.ponto}</span>
                      <p className="text-micro mt-0.5 text-lia-text-secondary">{pf.evidencia}</p>
                      <p className="text-micro mt-0.5 flex items-center gap-1">
                        <ArrowRight className="w-3 h-3" />
                        {pf.impacto_negocio}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {mockParecer.riscos_mitigacoes && mockParecer.riscos_mitigacoes.length > 0 && (
          <div className="mb-3">
            <div className="text-micro font-semibold mb-1.5 flex items-center gap-1 text-lia-text-secondary">
              <span className="w-4 h-4 rounded-full flex items-center justify-center text-micro font-bold bg-status-warning/[.12] text-status-warning">3</span>
              Riscos e Mitigações
            </div>
            <div className="space-y-1.5 pl-5">
              {mockParecer.riscos_mitigacoes.map((rm, idx) => {
                const nivelColor = rm.nivel === 'alto' ? 'var(--status-error)' : rm.nivel === 'medio' ? 'var(--status-warning)' : 'var(--lia-text-tertiary)'
                const nivelBgColor = rm.nivel === 'alto' ? 'var(--status-error-bg-15)' : rm.nivel === 'medio' ? 'var(--status-warning-bg-15)' : 'var(--lia-bg-tertiary)'
                return (
                  <div key={`rm-${idx}`} className="p-2 rounded-md" style={{borderLeft: `2px solid ${nivelColor}`}}>
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1">
                        <span className="text-xs font-medium text-lia-text-primary">{rm.risco}</span>
                        <p className="text-micro mt-0.5 text-lia-text-secondary">
                          <span className="font-medium">Mitigação:</span> {rm.mitigacao}
                        </p>
                      </div>
                      <div className="flex flex-col items-end gap-1">
                        <span
                          className="text-micro font-medium px-1.5 py-0.5 rounded-full"
                          style={{backgroundColor: nivelBgColor, color: nivelColor}}
                        >
                          Risco {rm.nivel === 'alto' ? 'Alto' : rm.nivel === 'medio' ? 'Médio' : 'Baixo'}
                        </span>
                        {rm.tempo_estimado && (
                          <span className="text-micro flex items-center gap-0.5 text-lia-text-secondary">
                            <Clock className="w-3 h-3" />
                            {rm.tempo_estimado}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {mockParecer.recomendacao_final && (
          <div>
            <div className="text-micro font-semibold mb-1.5 flex items-center gap-1 text-lia-text-secondary">
              <span className="w-4 h-4 rounded-full flex items-center justify-center text-micro font-bold" style={{backgroundColor: decisionBadge ? decisionBadge.bg : 'var(--wedo-cyan-bg-12)', color: decisionBadge ? decisionBadge.color : 'var(--lia-text-secondary)'}}>4</span>
              Recomendação Final
            </div>
            <div className="pl-5 p-2.5 rounded-xl border border-lia-border-subtle" style={{backgroundColor: decisionBadge ? decisionBadge.bg : 'var(--lia-bg-secondary)'}}>
              <p className="text-xs leading-relaxed mb-2 text-lia-text-primary">
                {mockParecer.recomendacao_final.justificativa}
              </p>
              {mockParecer.recomendacao_final.proximos_passos && mockParecer.recomendacao_final.proximos_passos.length > 0 && (
                <div>
                  <span className="text-micro font-medium text-lia-text-secondary">Próximos Passos:</span>
                  <ul className="mt-1 space-y-0.5">
                    {mockParecer.recomendacao_final.proximos_passos.map((ps, idx) => (
                      <li key={`ps-${idx}`} className="text-micro flex items-start gap-1.5 text-lia-text-primary">
                        <span className="text-lia-text-secondary">→</span>
                        {ps}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      <div className="p-3 border border-lia-border-subtle rounded-lg bg-lia-bg-secondary">
        <h3 className="text-xs font-semibold flex items-center gap-2 mb-2 text-lia-text-primary">
          <Lightbulb className="w-4 h-4 text-lia-text-secondary" />
          Por que este candidato?
        </h3>
        <div className="space-y-1.5">
          {mockWhyCandidate.map((reason, idx) => (
            <div key={`why-${idx}`} className="flex items-start gap-2 p-2 rounded-xl bg-lia-bg-secondary">
              <CheckCircle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-lia-text-secondary" />
              <span className="text-xs text-lia-text-primary">{reason}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
