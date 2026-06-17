"use client"

import React from "react"
import { Check, AlertTriangle, X, FileText, AlertCircle, Shield, BarChart3, ChevronDown, ChevronRight, CheckCircle, XCircle } from "lucide-react"
import type { RubricRequirement, RedFlag, RubricEvaluationData } from "./rubric-evaluation-types"
import {
  getEvaluationLevel,
  getRubricStyle,
  getRubricLabel,
  getPriorityLabel,
  getPriorityStyle,
} from "@/hooks/ai/use-rubric-evaluation"

function getRubricIcon(level: string) {
  switch (level?.toLowerCase()) {
    case 'exceeds':
      return <Check className="w-3.5 h-3.5 text-lia-text-secondary" />
    case 'meets':
      return <Check className="w-3.5 h-3.5 text-lia-text-secondary" />
    case 'partial':
      return <AlertTriangle className="w-3.5 h-3.5 text-status-warning" />
    case 'missing':
      return <X className="w-3.5 h-3.5 text-wedo-coral" />
    default:
      return <AlertCircle className="w-3.5 h-3.5 text-lia-text-secondary" />
  }
}

interface RubricDetailsSectionProps {
  sortedRequirements: RubricRequirement[]
  requirements: RubricRequirement[]
  mockRedFlags: RedFlag[]
  showAudit: boolean
  setShowAudit: (value: boolean) => void
  essentialMet: number
  essentialReqsLength: number
  evaluation: RubricEvaluationData
}

export function RubricDetailsSection({
  sortedRequirements,
  requirements,
  mockRedFlags,
  showAudit,
  setShowAudit,
  essentialMet,
  essentialReqsLength,
  evaluation,
}: RubricDetailsSectionProps) {
  return (
    <div className="space-y-3">
      <div className="p-3 border border-lia-border-subtle rounded-lg bg-lia-bg-secondary">
        <h3 className="text-xs font-semibold flex items-center gap-2 mb-2 text-lia-text-primary">
          <FileText className="w-4 h-4 text-lia-text-secondary" />
          Matriz de Avaliação por Requisito
        </h3>
        <div className="space-y-2">
          {sortedRequirements.map((req, idx) => {
            const level = getEvaluationLevel(req)
            const reqName = req.name || req.requirement
            const rubricStyle = getRubricStyle(level)
            const priorityStyle = getPriorityStyle(req.priority)
            return (
              <div
                key={`req-${idx}`}
                className="p-2.5 rounded-md transition-colors motion-reduce:transition-none"
                style={{backgroundColor: rubricStyle.bg, border: `1px solid ${rubricStyle.border}`}}
              >
                <div className="flex items-start gap-2">
                  <div className="mt-0.5 flex-shrink-0">
                    {getRubricIcon(level)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5 flex-wrap mb-0.5">
                      <span className="text-xs font-medium text-lia-text-primary">{reqName}</span>
                      {req.priority && (
                        <span
                          className="text-micro font-medium px-1.5 py-0 rounded-full"
                          style={{backgroundColor: priorityStyle.bg, color: priorityStyle.color}}
                        >
                          {getPriorityLabel(req.priority)}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-1">
                      <span className="text-micro font-medium" style={{color: rubricStyle.color}}>
                        {getRubricLabel(level)}
                      </span>
                      {req.evidence && (
                        <>
                          <span className="text-lia-text-tertiary">•</span>
                          <span className="text-micro text-lia-text-secondary">{req.evidence}</span>
                        </>
                      )}
                    </div>
                    {req.narrative && (
                      <p className="text-micro mt-1 text-lia-text-secondary">{req.narrative}</p>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
          {sortedRequirements.length === 0 && (
            <div className="text-center py-4 text-xs text-lia-text-secondary">
              Nenhum requisito avaliado disponível.
            </div>
          )}
        </div>
      </div>

      <div className="p-3 border border-lia-border-subtle rounded-lg bg-lia-bg-secondary">
        <h3 className="text-xs font-semibold flex items-center gap-2 mb-2 text-lia-text-primary">
          <Shield className="w-4 h-4 text-lia-text-secondary" />
          Verificação de Red Flags
        </h3>
        <div className="space-y-1.5">
          {mockRedFlags.map((flag, idx) => {
            const statusIcon = flag.status === 'ok' ? CheckCircle : flag.status === 'warning' ? AlertTriangle : XCircle
            const statusColor = flag.status === 'ok' ? 'var(--lia-btn-primary-bg)' : flag.status === 'warning' ? 'var(--status-warning)' : 'var(--status-error)'
            return (
              <div key={`rf-${idx}`} className="flex items-center justify-between p-2 rounded-xl bg-lia-bg-secondary">
                <span className="text-xs text-lia-text-primary">{flag.type}</span>
                <div className="flex items-center gap-1.5">
                  {flag.detail && (
                    <span className="text-micro text-lia-text-secondary">{flag.detail}</span>
                  )}
                  {React.createElement(statusIcon, { className: "w-3.5 h-3.5", style: { color: statusColor } })}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      <div className="p-3 border border-lia-border-subtle rounded-lg bg-lia-bg-secondary">
        <button
          onClick={() => setShowAudit(!showAudit)}
          className="w-full flex items-center justify-between text-xs font-semibold text-lia-text-primary hover:bg-lia-interactive-hover transition-colors cursor-pointer"
        >
          <span className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-lia-text-secondary" />
            Métricas de Auditoria
          </span>
          {showAudit ? (
            <ChevronDown className="w-4 h-4 text-lia-text-secondary" />
          ) : (
            <ChevronRight className="w-4 h-4 text-lia-text-secondary" />
          )}
        </button>

        {showAudit && (
          <div className="mt-3 pt-3 border-t border-t-lia-border-subtle">
            <div className="grid grid-cols-2 gap-2 mb-3">
              <div className="p-2 rounded-xl bg-lia-bg-secondary">
                <div className="text-micro text-lia-text-secondary">Total Requisitos</div>
                <div className="text-sm font-bold text-lia-text-primary">{requirements.length}</div>
              </div>
              <div className="p-2 rounded-xl bg-lia-bg-secondary">
                <div className="text-micro text-lia-text-secondary">Red Flags</div>
                <div className={`text-sm font-bold ${mockRedFlags.filter(f => f.status !== 'ok').length > 0 ? 'text-status-warning' : 'text-lia-text-secondary'}`}>
                  {mockRedFlags.filter(f => f.status !== 'ok').length}
                </div>
              </div>
              <div className="p-2 rounded-xl bg-lia-bg-secondary">
                <div className="text-micro text-lia-text-secondary">Taxa Essenciais</div>
                <div className={`text-sm font-bold ${essentialMet === essentialReqsLength ? 'text-lia-btn-primary-bg' : 'text-status-warning'}`}>
                  {essentialReqsLength > 0 ? Math.round((essentialMet / essentialReqsLength) * 100) : 100}%
                </div>
              </div>
              <div className="p-2 rounded-xl bg-lia-bg-secondary">
                <div className="text-micro text-lia-text-secondary">Tempo Análise</div>
                <div className="text-sm font-bold text-lia-text-primary">
                  {evaluation.audit_metrics?.analysis_time || '2.3'}s
                </div>
              </div>
            </div>

            <div className="text-micro font-medium mb-1.5 text-lia-text-secondary">Legenda de Níveis</div>
            <div className="grid grid-cols-4 gap-1">
              {[
                { code: 'E+', label: 'Excede', color: undefined, bgColor: undefined },
                { code: 'A', label: 'Atende', color: undefined, bgColor: undefined },
                { code: 'P', label: 'Parcial', color: 'var(--status-warning)', bgColor: 'var(--status-warning-bg-15)' },
                { code: 'X', label: 'Ausente', color: 'var(--status-error)', bgColor: 'var(--status-error-bg-15)' },
              ].map((item, idx) => (
                <div key={`detail-${idx}`} className="flex items-center gap-1 p-1.5 rounded-xl bg-lia-bg-secondary">
                  <span
                    className="text-micro font-bold w-5 h-5 flex items-center justify-center rounded-md"
                    style={{backgroundColor: item.bgColor, color: item.color}}
                  >
                    {item.code}
                  </span>
                  <span className="text-micro text-lia-text-secondary">{item.label}</span>
                </div>
              ))}
            </div>

            <div className="mt-2 pt-2 space-y-1 border-t border-t-lia-border-subtle">
              {[
                { label: 'Versão', value: 'IA CV Analyzer v1.0' },
                { label: 'Data/Hora', value: new Date().toLocaleString('pt-BR') },
              ].map((item, idx) => (
                <div key={`just-${idx}`} className="flex items-center justify-between">
                  <span className="text-micro text-lia-text-secondary">{item.label}</span>
                  <span className="text-micro font-medium text-lia-text-primary">{item.value}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
