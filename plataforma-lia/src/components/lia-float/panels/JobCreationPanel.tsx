"use client"

import React from "react"
import { FileText, CheckCircle2, Circle, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"

interface JobField {
  label: string
  value: string
  status: "complete" | "in_progress" | "pending"
}

interface JobCreationPanelProps {
  data: Record<string, unknown>
  onUpdateData?: (data: Record<string, unknown>) => void
}

export function JobCreationPanel({ data }: JobCreationPanelProps) {
  const title = (data.title as string) || "Nova Vaga"
  const jdPreview = (data.jd_preview as string) || ""
  const step = (data.current_step as number) || 1
  const totalSteps = (data.total_steps as number) || 5

  const fields: JobField[] = (data.fields as JobField[]) || [
    { label: "Título da vaga", value: title, status: title ? "complete" : "pending" },
    { label: "Departamento", value: (data.department as string) || "", status: data.department ? "complete" : "pending" },
    { label: "Localização", value: (data.location as string) || "", status: data.location ? "complete" : "pending" },
    { label: "Tipo de contrato", value: (data.contract_type as string) || "", status: data.contract_type ? "complete" : "pending" },
    { label: "Faixa salarial", value: (data.salary_range as string) || "", status: data.salary_range ? "complete" : "pending" },
    { label: "Requisitos", value: (data.requirements as string) || "", status: data.requirements ? "complete" : "pending" },
    { label: "Descrição", value: jdPreview ? "Gerada" : "", status: jdPreview ? "complete" : "pending" },
  ]

  const completedFields = fields.filter(f => f.status === "complete").length
  const progressPercent = Math.round((completedFields / fields.length) * 100)

  return (
    <div className="flex flex-col h-full">
      <div className="px-4 py-3 flex items-center gap-2">
        <FileText className="w-4 h-4 text-wedo-cyan" />
        <span className="text-sm font-semibold text-lia-text-primary">Criação de Vaga</span>
      </div>

      <div className="px-4 py-3">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-lia-text-secondary">Progresso</span>
          <span className="text-xs font-medium text-lia-text-primary">
            Passo {step}/{totalSteps} — {completedFields}/{fields.length} campos
          </span>
        </div>
        <div className="w-full h-2 rounded-full bg-lia-bg-tertiary overflow-hidden">
          <div
            className="h-full rounded-full bg-wedo-cyan transition-[width] duration-500"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        <div className="px-4 py-3 space-y-2">
          <p className="text-micro font-semibold text-lia-text-tertiary uppercase tracking-wider mb-2">Campos</p>
          {fields.map((f, i) => (
            <div key={i} className="flex items-start gap-2 py-1.5">
              {f.status === "complete" ? (
                <CheckCircle2 className="w-4 h-4 text-status-success flex-shrink-0 mt-0.5" />
              ) : f.status === "in_progress" ? (
                <Loader2 className="w-4 h-4 text-wedo-cyan animate-spin flex-shrink-0 mt-0.5" />
              ) : (
                <Circle className="w-4 h-4 text-lia-text-muted flex-shrink-0 mt-0.5" />
              )}
              <div className="flex-1 min-w-0">
                <p className={cn(
                  "text-xs",
                  f.status === "complete" ? "text-lia-text-primary" : "text-lia-text-disabled"
                )}>
                  {f.label}
                </p>
                {f.value && f.status === "complete" && (
                  <p className="text-micro text-lia-text-secondary truncate">{f.value}</p>
                )}
              </div>
            </div>
          ))}
        </div>


        {/* Benefits */}
        {!!(data.confirmed_benefits || data.confirmed_variable_compensation) && (
          <div className="px-4 py-3 border-t border-lia-border-subtle">
            <p className="text-micro font-semibold text-lia-text-tertiary uppercase tracking-wider mb-2">Benefícios</p>
            {Array.isArray(data.confirmed_benefits) ? (data.confirmed_benefits as string[]).map((b, i) => (
              <div key={i} className="flex items-center gap-2 py-1">
                <CheckCircle2 className="w-3.5 h-3.5 text-status-success flex-shrink-0" />
                <p className="text-xs text-lia-text-primary">{String(b)}</p>
              </div>
            )) : null}
            {Array.isArray(data.confirmed_variable_compensation) ? (
              <div className="mt-1">
                <p className="text-micro text-lia-text-tertiary uppercase tracking-wider mb-1">Remuneração Variável</p>
                {(data.confirmed_variable_compensation as string[]).map((v, i) => (
                  <div key={i} className="flex items-center gap-2 py-1">
                    <CheckCircle2 className="w-3.5 h-3.5 text-status-success flex-shrink-0" />
                    <p className="text-xs text-lia-text-primary">{String(v)}</p>
                  </div>
                ))}
              </div>
            ) : null}
          </div>
        )}

        {jdPreview && (
          <div className="px-4 py-3 border-t border-lia-border-subtle">
            <p className="text-micro font-semibold text-lia-text-tertiary uppercase tracking-wider mb-2">Preview do JD</p>
            <div className="p-3 rounded-lg bg-lia-bg-secondary border border-lia-border-subtle">
              <p className="text-xs text-lia-text-primary whitespace-pre-wrap leading-relaxed">
                {jdPreview.length > 500 ? jdPreview.slice(0, 500) + "..." : jdPreview}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
