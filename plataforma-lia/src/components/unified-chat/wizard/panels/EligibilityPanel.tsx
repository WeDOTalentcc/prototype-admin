"use client"

import React from "react"
import { ShieldCheck, Plus } from "lucide-react"
import type { EligibilityData } from "../wizard-types"

interface Props {
  data: Record<string, unknown>
  onUpdate?: (updates: Record<string, unknown>) => void
}

export function EligibilityPanel({ data }: Props) {
  const d = data as unknown as EligibilityData
  const questions = d.questions || []

  return (
    <div className="px-4 py-3 space-y-3">
      <div className="flex items-center gap-1.5">
        <ShieldCheck className="w-4 h-4 text-wedo-cyan" />
        <span className="text-xs font-medium text-lia-text-secondary font-['Open_Sans',sans-serif]">
          Perguntas eliminatorias ({questions.length})
        </span>
      </div>

      {questions.length > 0 ? (
        <div className="space-y-2">
          {questions.map((q, i) => (
            <div key={i} className="flex items-start gap-2 p-2.5 rounded-md border border-lia-border-subtle">
              <span className="flex-shrink-0 w-5 h-5 rounded-full bg-status-error/10 text-status-error flex items-center justify-center text-[10px] font-medium mt-0.5">!</span>
              <div className="flex-1">
                <p className="text-sm text-lia-text-primary font-['Open_Sans',sans-serif]">{q.question}</p>
                <p className="text-[10px] text-lia-text-tertiary font-['Open_Sans',sans-serif] mt-0.5">
                  Resposta obrigatoria: {q.required_answer === "yes" ? "Sim" : "Nao"}
                </p>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-xs text-lia-text-tertiary font-['Open_Sans',sans-serif]">
          Nenhuma pergunta eliminatoria configurada. Diga no chat para adicionar.
        </p>
      )}
    </div>
  )
}
