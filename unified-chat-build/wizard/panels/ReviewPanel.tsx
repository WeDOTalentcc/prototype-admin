"use client"

import React from "react"
import { CheckCircle, XCircle, ClipboardCheck, Settings } from "lucide-react"
import type { ReviewData } from "../wizard-types"

interface Props {
  data: Record<string, unknown>
  onUpdate?: (updates: Record<string, unknown>) => void
}

const CHECK_LABELS: Record<string, string> = {
  jd_approved: "JD aprovado pelo recrutador",
  questions_approved: "Perguntas aprovadas",
  has_questions: "Perguntas geradas",
  has_seniority: "Senioridade definida",
  quality_score_ok: "Quality score >= 50",
  has_eligibility: "Elegibilidade configurada",
  has_salary: "Faixa salarial definida",
}

export function ReviewPanel({ data, onUpdate }: Props) {
  const d = data as unknown as ReviewData
  const readiness = d.readiness || { ready: false, checks: {}, missing: [] }
  const defaultsApplied = d.defaults_applied || []

  const handleApplyDefaults = () => {
    window.dispatchEvent(new CustomEvent("lia:prefill-message", {
      detail: { message: "Aplicar defaults da empresa nesta vaga" },
    }))
  }

  return (
    <div className="px-4 py-3 space-y-3">
      <div className="flex items-center gap-2">
        <ClipboardCheck className="w-4 h-4 text-wedo-cyan" />
        <span className="text-sm font-semibold text-lia-text-primary font-['Open_Sans',sans-serif]">
          Checklist de publicacao
        </span>
      </div>

      <div className="space-y-1.5">
        {Object.entries(readiness.checks || {}).map(([key, passed]) => (
          <div key={key} className="flex items-center gap-2 text-sm font-['Open_Sans',sans-serif]">
            {passed ? (
              <CheckCircle className="w-4 h-4 text-status-success flex-shrink-0" />
            ) : (
              <XCircle className="w-4 h-4 text-status-error flex-shrink-0" />
            )}
            <span className={passed ? "text-lia-text-primary" : "text-status-error"}>
              {CHECK_LABELS[key] || key}
            </span>
          </div>
        ))}
      </div>

      {readiness.ready ? (
        <div className="p-2.5 rounded-md bg-status-success/5 border border-status-success/20">
          <p className="text-xs text-status-success font-medium font-['Open_Sans',sans-serif]">
            Vaga pronta para publicar!
          </p>
        </div>
      ) : (
        <div className="p-2.5 rounded-md bg-status-warning/5 border border-status-warning/20">
          <p className="text-xs text-status-warning font-medium font-['Open_Sans',sans-serif]">
            Pendencias: {readiness.missing?.join(", ")}
          </p>
        </div>
      )}

      {/* Applied defaults */}
      {defaultsApplied.length > 0 && (
        <div className="text-[10px] text-lia-text-tertiary font-['Open_Sans',sans-serif]">
          Defaults aplicados: {defaultsApplied.join(", ")}
        </div>
      )}

      {/* Apply defaults button */}
      {!readiness.ready && (
        <button
          onClick={handleApplyDefaults}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-md border border-lia-border-subtle text-xs font-medium text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors font-['Open_Sans',sans-serif]"
        >
          <Settings className="w-3.5 h-3.5" />
          Aplicar defaults da empresa
        </button>
      )}
    </div>
  )
}
