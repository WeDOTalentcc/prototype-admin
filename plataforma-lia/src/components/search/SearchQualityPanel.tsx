"use client"

/**
 * SearchQualityPanel — Painel de qualidade da busca com barra de completude,
 * alertas inteligentes e ação recomendada.
 *
 * Extraído de ExpandableAIPrompt (P1-E).
 * Portabilidade Vue: mapeia para componente SearchQualityPanel.vue.
 */

import React from "react"
import { TrendingUp, AlertTriangle, Info } from "lucide-react"
import type { SearchAnalysis } from "@/components/search/expandable-ai-prompt.types"

interface SearchQualityPanelProps {
  searchAnalysis: SearchAnalysis
  /** Chamado quando o usuário clica em uma sugestão de alerta para inserir o valor na busca */
  onAlertActionClick: (value: string) => void
}

export function SearchQualityPanel({ searchAnalysis, onAlertActionClick }: SearchQualityPanelProps) {
  const score = searchAnalysis.completeness_score

  const scoreColor =
    score >= 60 ? 'var(--status-success)' : score >= 40 ? 'var(--status-warning)' : 'var(--status-error)'

  return (
    <div className="space-y-2 pt-2 mt-2 border-t border-lia-border-default dark:border-lia-border-default">
      {/* Barra de completude */}
      <div className="flex items-center gap-3">
        <div className="flex-1">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-medium text-lia-text-secondary">
              Qualidade da busca
            </span>
            <span className="text-xs font-bold" style={{color: scoreColor}}>
              {score}%
            </span>
          </div>
          <div className="h-1.5 rounded-full overflow-hidden bg-lia-bg-tertiary dark:bg-lia-bg-secondary">
            <div
              className="h-full rounded-full transition-[width,height] duration-500"
              style={{width: `${score}%`, backgroundColor: scoreColor}}
            />
          </div>
        </div>

        {searchAnalysis.next_recommended_action && (
          <div
            className="flex items-center gap-1.5 px-2 py-1 rounded-full text-xs bg-wedo-cyan/[.08]"
          >
            <TrendingUp className="w-3 h-3" />
            <span>{searchAnalysis.next_recommended_action}</span>
          </div>
        )}
      </div>

      {/* Alertas inteligentes */}
      {searchAnalysis.alerts.length > 0 && (
        <div className="space-y-1.5">
          {searchAnalysis.alerts.slice(0, 2).map((alert, index) => (
            <div
              key={`alert-${index}`}
              className="flex items-start gap-2 px-2.5 py-2 rounded-full text-xs"
              style={{backgroundColor:
                  alert.severity === 'warning'
                    ? 'var(--status-warning-bg-08)'
                    : 'var(--wedo-cyan-bg-08)',
                color: 'var(--lia-text-secondary)'}}
            >
              {alert.severity === 'warning' ? (
                <AlertTriangle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-status-warning" />
              ) : (
                <Info className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-lia-text-secondary" />
              )}
              <div className="flex-1 min-w-0">
                <span>{alert.message}</span>
                {alert.suggestion && alert.action_value && (
                  <button
                    onClick={() => onAlertActionClick(alert.action_value!)}
                    className="ml-1 font-medium hover:underline text-lia-text-primary"
                  >
                    {alert.suggestion}
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
