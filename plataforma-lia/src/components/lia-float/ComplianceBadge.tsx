"use client"

import React from "react"
import { ShieldCheck } from "lucide-react"
import { cn } from "@/lib/utils"

/**
 * Texto canônico da claim de anonimização (ADR-LGPD-002).
 * DEVE refletir o que `strip_pii_for_llm_prompt` faz de fato — pinado pelo sensor
 * backend tests/contract/test_compliance_badge_claim.py. NÃO alterar a claim sem
 * estender o mecanismo + o sensor (proveniência honesta / anti-ghost).
 */
export const COMPLIANCE_ANON_CLAIM =
  "Identificadores sensíveis (CPF, e-mail, telefone) são anonimizados antes do processamento por IA"

/**
 * Badge "compliance by design" — comunica ao recrutador que identificadores
 * sensíveis são anonimizados ANTES de irem ao provedor de IA (vendor). Refere-se
 * ao processamento por IA, NÃO ao que o recrutador vê (ele vê o dado completo).
 * Puramente presentational (design tokens, zero lógica).
 */
export function ComplianceBadge({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "flex items-center justify-center gap-1 mt-1.5 text-micro text-lia-text-tertiary select-none",
        className,
      )}
      title={COMPLIANCE_ANON_CLAIM}
      aria-label={COMPLIANCE_ANON_CLAIM}
    >
      <ShieldCheck className="w-3 h-3 flex-shrink-0" aria-hidden="true" />
      <span className="truncate">Dados sensíveis anonimizados antes da IA</span>
    </div>
  )
}
