"use client"

/**
 * LiaImpactSummary — P1-9 (audit 2026-05-26):
 *
 * Torna VISÍVEL o diferencial competitivo invisível da WeDOTalent —
 * a única plataforma que tem CompanyProfile estruturado consumido por
 * agentes IA em múltiplos contextos. Antes deste componente, o admin
 * via uma lista plana de 34 toggles sem entender o IMPACTO real de
 * cada campo nas decisões da LIA.
 *
 * Estrutura visual:
 *  1. Stat: X de 34 campos canonical visíveis à LIA (toggle ON)
 *  2. Stat: N contextos de uso (sourcing, screening, JD, persona, BigFive)
 *  3. Exemplos concretos por campo → contexto (educacional)
 *
 * Audit ref: ~/Documents/wedotalent_audit_2026-05-26/CONFIGURACOES_MENU_COHERENCE_AUDIT.md
 * P1-9 + §7.3 P6 ("Diferencial competitivo invisível").
 *
 * Cyan exclusivo (CLAUDE.md plataforma-lia DS v4.2.1: wedo-cyan = elementos LIA/IA).
 */

import { Brain, Database, Zap, ArrowRight } from "lucide-react"
import {
  LIA_FIELD_DEFINITIONS,
  type LiaFieldKey,
} from "@/hooks/company/use-company-lia-instructions"

interface Props {
  toggles: Partial<Record<LiaFieldKey, boolean>>
}

/**
 * Mapping field_key → exemplo conciso de "para que a LIA usa".
 * Selected fields with high recruiter-comprehension impact (não exaustivo —
 * 6 examples are enough to communicate o pattern; cobrir 34 viraria poluição).
 */
const FIELD_USAGE_EXAMPLES: Array<{ field: LiaFieldKey | string; usage: string }> = [
  { field: "mission", usage: "tom dos textos de vaga" },
  { field: "values", usage: "match cultural com candidatos" },
  { field: "tech_stack", usage: "calibração de perguntas técnicas" },
  { field: "company_big_five", usage: "perfil ideal de candidato" },
  { field: "evp_bullets", usage: "destaques no convite ao candidato" },
  { field: "seniority_levels", usage: "ranking automático por nível" },
]

const TOTAL_CONTEXTS = 5 // sourcing, cv_screening, job_creation, persona, learning loops

export function LiaImpactSummary({ toggles }: Props) {
  const totalCanonical = Object.keys(LIA_FIELD_DEFINITIONS).length
  // Default canonical: toggles iniciam ON. Considera explicitamente OFF apenas
  // os que vieram false do backend; ausente = ON (compat com DEFAULT_FIELD_TOGGLES).
  const activeCount = Object.keys(LIA_FIELD_DEFINITIONS).filter((key) => {
    const v = toggles[key as LiaFieldKey]
    return v !== false
  }).length

  const percentVisible = Math.round((activeCount / totalCanonical) * 100)

  return (
    <div
      className="space-y-3 p-4 rounded-xl border border-wedo-cyan/40 bg-gradient-to-br from-wedo-cyan/10 to-transparent dark:from-wedo-cyan/15 dark:to-transparent"
      data-testid="lia-impact-summary"
    >
      <div className="flex items-center gap-2">
        <Brain className="w-5 h-5 text-wedo-cyan shrink-0" aria-hidden="true" />
        <h4 className="text-sm font-semibold text-lia-text-primary dark:text-lia-text-primary">
          Sua LIA está usando dados estruturados da sua empresa
        </h4>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div className="flex items-start gap-2">
          <Database className="w-4 h-4 text-wedo-cyan shrink-0 mt-0.5" aria-hidden="true" />
          <div className="text-sm leading-snug">
            <span className="font-semibold text-lia-text-primary">
              {activeCount} de {totalCanonical}
            </span>
            <span className="text-lia-text-secondary"> ({percentVisible}%)</span>
            <p className="text-xs text-lia-text-secondary mt-0.5">
              campos canonical visíveis para a LIA
            </p>
          </div>
        </div>

        <div className="flex items-start gap-2">
          <Zap className="w-4 h-4 text-wedo-cyan shrink-0 mt-0.5" aria-hidden="true" />
          <div className="text-sm leading-snug">
            <span className="font-semibold text-lia-text-primary">
              {TOTAL_CONTEXTS}+ contextos
            </span>
            <p className="text-xs text-lia-text-secondary mt-0.5">
              onde a LIA aplica esses dados (sourcing, triagem, JD, persona, learning loops)
            </p>
          </div>
        </div>
      </div>

      <div className="border-t border-wedo-cyan/20 pt-2 space-y-1">
        <p className="text-xs font-medium text-lia-text-primary">
          Como a LIA usa cada campo:
        </p>
        <ul className="space-y-0.5">
          {FIELD_USAGE_EXAMPLES.map(({ field, usage }) => {
            const def = LIA_FIELD_DEFINITIONS[field as LiaFieldKey]
            const label = def?.label ?? field
            return (
              <li
                key={field}
                className="flex items-center gap-1.5 text-xs text-lia-text-secondary"
              >
                <span className="font-medium text-lia-text-primary">{label}</span>
                <ArrowRight className="w-3 h-3 text-wedo-cyan shrink-0" aria-hidden="true" />
                <span>{usage}</span>
              </li>
            )
          })}
        </ul>
      </div>

      {activeCount < totalCanonical && (
        <p className="text-xs text-lia-text-secondary border-t border-wedo-cyan/20 pt-2">
          {totalCanonical - activeCount} {totalCanonical - activeCount === 1 ? "campo está" : "campos estão"} ocultos da LIA. Use os toggles abaixo para ajustar.
        </p>
      )}
    </div>
  )
}
