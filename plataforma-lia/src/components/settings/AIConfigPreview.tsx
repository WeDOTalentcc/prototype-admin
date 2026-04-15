"use client"

import React from "react"
import { Brain, User } from "lucide-react"
import { cn } from "@/lib/utils"
import { textStyles } from "@/lib/design-tokens"

const TONE_PREVIEWS: Record<string, { question: string; answer: string }> = {
  professional: {
    question: "Quantos candidatos temos para a vaga de Desenvolvedor?",
    answer:
      "Atualmente, a vaga de Desenvolvedor Senior conta com 23 candidatos ativos no pipeline. " +
      "Destes, 8 estao na fase de triagem, 10 em entrevista tecnica e 5 aguardando entrevista final. " +
      "Posso detalhar o perfil de algum candidato especifico?",
  },
  casual: {
    question: "Quantos candidatos temos para a vaga de Desenvolvedor?",
    answer:
      "Temos 23 candidatos! 8 na triagem, 10 na tecnica e 5 quase no final. " +
      "Quer que eu destaque os top 3?",
  },
  concise: {
    question: "Quantos candidatos temos para a vaga de Desenvolvedor?",
    answer: "23 candidatos. 8 triagem, 10 tecnica, 5 final.",
  },
  detailed: {
    question: "Quantos candidatos temos para a vaga de Desenvolvedor?",
    answer:
      "A vaga de Desenvolvedor Senior (#DEV-042) possui 23 candidatos distribuidos em 3 etapas: " +
      "Triagem (8 — taxa de conversao 65%), Entrevista Tecnica (10 — nota media WSI 4.2/5), " +
      "Entrevista Final (5 — todos com score >85%). Comparado ao mercado, o funil esta 15% acima da media.",
  },
}

interface AIConfigPreviewProps {
  tone: string
  compact?: boolean
  className?: string
}

export function AIConfigPreview({ tone, compact = false, className }: AIConfigPreviewProps) {
  const preview = TONE_PREVIEWS[tone] || TONE_PREVIEWS.professional

  return (
    <div className={cn("space-y-2", className)}>
      {!compact && (
        <p className={cn(textStyles.caption, "uppercase tracking-wider")}>Preview da resposta</p>
      )}

      {/* Recruiter question */}
      <div className="flex items-start gap-2">
        <div className="w-5 h-5 rounded-full bg-lia-bg-tertiary dark:bg-lia-bg-primary flex items-center justify-center flex-shrink-0 mt-0.5">
          <User className="w-3 h-3 text-lia-text-tertiary" aria-hidden="true" />
        </div>
        <p className={cn(textStyles.body, compact ? "text-[10px]" : "text-xs")}>
          {preview.question}
        </p>
      </div>

      {/* LIA response */}
      <div className="flex items-start gap-2">
        <div className="w-5 h-5 rounded-full bg-wedo-cyan/15 dark:bg-wedo-cyan/20 flex items-center justify-center flex-shrink-0 mt-0.5">
          <Brain className="w-3 h-3 text-wedo-cyan" aria-hidden="true" />
        </div>
        <div
          className={cn(
            "border-l-2 border-wedo-cyan/30 pl-2.5 flex-1",
            compact ? "text-[10px]" : "text-xs"
          )}
        >
          <p className="text-lia-text-primary dark:text-lia-text-primary leading-relaxed">
            {preview.answer}
          </p>
        </div>
      </div>
    </div>
  )
}
