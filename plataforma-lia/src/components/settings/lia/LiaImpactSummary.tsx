"use client"

/**
 * LiaImpactSummary — tab "Visibilidade" em LiaPersonalizacaoHub.
 *
 * Painel de transparência: mostra ao recrutador exatamente quais dados
 * estão sendo enviados para a IA agora. 3 seções:
 *
 *   A. Campos LIA ativos — contagem de 34 toggles + breakdown por categoria
 *   B. Perfil da empresa preenchido — quais seções têm conteúdo real
 *   C. Capacidades de aprendizado (Learning Loops) — 4 gates ativos/inativos
 *
 * Reutiliza queries existentes:
 *   - useCompanyLiaInstructions() para toggles + config cultural
 *   - fetch /api/backend-proxy/companies/{id}/learning-loops-config (mesmo endpoint de LearningLoopsPanel)
 *
 * Design: Quiet Operator — 90% gray scale, sem cyan, flat (sem card wrappers).
 * CLAUDE.md: gray-only progress bars, ●/○ para status, font-size xs/[10px].
 *
 * Ref: CONFIGURACOES_MENU_COHERENCE_AUDIT.md §P1-9 / audit 2026-05-26.
 */

import React, { useEffect, useState, useCallback } from "react"
import useCompanyId from "@/hooks/company/useCompanyId"
import {
  useCompanyLiaInstructions,
  LIA_FIELD_DEFINITIONS,
  type LiaFieldKey,
} from "@/hooks/company/use-company-lia-instructions"

// ── Category grouping ──────────────────────────────────────────────────────
const CATEGORY_ORDER = [
  "Informações da Empresa",
  "Cultura & Identidade",
  "Trabalho & Contratação",
  "Estrutura Organizacional",
  "EVP",
  "Tecnologia",
  "Recrutamento",
  "Planejamento",
  "ESG & Impacto",
] as const

type CategoryName = (typeof CATEGORY_ORDER)[number]

function buildCategories(
  toggles: Partial<Record<LiaFieldKey, boolean>>,
): Array<{ id: CategoryName; label: string; activeCount: number; totalCount: number }> {
  const counts: Record<string, { active: number; total: number }> = {}
  for (const [key, def] of Object.entries(LIA_FIELD_DEFINITIONS)) {
    const cat = def.category as string
    if (!counts[cat]) counts[cat] = { active: 0, total: 0 }
    counts[cat].total++
    const v = toggles[key as LiaFieldKey]
    if (v !== false) counts[cat].active++ // default ON per DEFAULT_FIELD_TOGGLES
  }
  return CATEGORY_ORDER.filter((c) => counts[c] !== undefined).map((c) => ({
    id: c,
    label: c,
    activeCount: counts[c].active,
    totalCount: counts[c].total,
  }))
}

// ── Profile sections derived from culture config ───────────────────────────
interface ProfileSection {
  id: string
  label: string
  isFilled: boolean
  detail?: string
}

// ── Learning loops config (same shape as LearningLoopsPanel) ─────────────
interface LearningLoopsConfig {
  enabled: boolean
  bigfive_company_culture: boolean
  bigfive_department_history: boolean
  wsi_question_effectiveness: boolean
  jd_similar_suggestion: boolean
}

const DEFAULT_LOOPS: LearningLoopsConfig = {
  enabled: true,
  bigfive_company_culture: true,
  bigfive_department_history: false,
  wsi_question_effectiveness: false,
  jd_similar_suggestion: true,
}

const LOOP_LABELS: Array<{ key: keyof LearningLoopsConfig; label: string }> = [
  { key: "bigfive_company_culture", label: "DNA Cultural da Empresa" },
  { key: "bigfive_department_history", label: "Histórico por Departamento" },
  { key: "jd_similar_suggestion", label: "Sugestão de JD Similar" },
  { key: "wsi_question_effectiveness", label: "Efetividade de Perguntas WSI" },
]

// ── Component ─────────────────────────────────────────────────────────────
export function LiaImpactSummary() {
  const { companyId } = useCompanyId()
  const { config, isLoading: isLoadingLia } = useCompanyLiaInstructions()

  const [loopsConfig, setLoopsConfig] = useState<LearningLoopsConfig>(DEFAULT_LOOPS)
  const [isLoadingLoops, setIsLoadingLoops] = useState(true)

  const fetchLoops = useCallback(async () => {
    if (!companyId) return
    setIsLoadingLoops(true)
    try {
      const res = await fetch(
        `/api/backend-proxy/companies/${encodeURIComponent(companyId)}/learning-loops-config`,
      )
      if (res.ok) {
        const data = await res.json()
        setLoopsConfig({ ...DEFAULT_LOOPS, ...data })
      }
    } catch {
      // Silently fall back to defaults — not a blocking failure for a summary panel
    } finally {
      setIsLoadingLoops(false)
    }
  }, [companyId])

  useEffect(() => {
    fetchLoops()
  }, [fetchLoops])

  // ── Section A: toggle counts ─────────────────────────────────────────
  const toggles = config?.lia_field_toggles ?? {}
  const totalCanonical = Object.keys(LIA_FIELD_DEFINITIONS).length
  const activeCount = Object.keys(LIA_FIELD_DEFINITIONS).filter(
    (k) => toggles[k as LiaFieldKey] !== false,
  ).length
  const categories = buildCategories(toggles)

  // ── Section B: company profile sections ──────────────────────────────
  const profileSections: ProfileSection[] = [
    {
      id: "mission_vision",
      label: "Missão e Visão",
      isFilled: !!(config?.mission || config?.vision),
    },
    {
      id: "values",
      label: "Valores",
      isFilled: !!(config?.values && config.values.length > 0),
      detail: config?.values?.length ? `${config.values.length} valores` : undefined,
    },
    {
      id: "benefits",
      label: "Benefícios",
      isFilled: !!(config?.benefits && config.benefits.length > 0),
      detail: config?.benefits?.length ? `${config.benefits.length} cadastrados` : undefined,
    },
    {
      id: "tech_stack",
      label: "Tech Stack",
      isFilled: !!config?.tech_stack && Object.values(config.tech_stack).flat().length > 0,
      detail:
        config?.tech_stack
          ? `${Object.values(config.tech_stack).flat().length} tecnologias`
          : undefined,
    },
    {
      id: "departments",
      label: "Departamentos",
      isFilled: !!(config?.departments && config.departments.length > 0),
      detail: config?.departments?.length
        ? `${config.departments.length} departamentos`
        : undefined,
    },
    {
      id: "evp",
      label: "Proposta de Valor (EVP)",
      isFilled: !!(config?.evp_bullets && config.evp_bullets.length > 0),
    },
    {
      id: "big_five",
      label: "Perfil Big Five",
      isFilled: !!config?.company_big_five,
    },
  ]

  const isLoading = isLoadingLia || isLoadingLoops
  const masterLoopEnabled = loopsConfig.enabled

  if (isLoading) {
    return (
      <div className="py-6 flex justify-center">
        <span className="text-xs text-lia-text-disabled">Carregando...</span>
      </div>
    )
  }

  return (
    <div className="space-y-8" data-testid="lia-impact-summary-panel">
      {/* Header */}
      <div>
        <h3 className="text-sm font-semibold text-lia-text-primary">O que a LIA está usando agora</h3>
        <p className="text-xs text-lia-text-tertiary mt-0.5">
          Transparência sobre os dados enviados para o sistema de IA nas interações com candidatos.
        </p>
      </div>

      {/* ── Section A: Campos LIA ativos ────────────────────────────────── */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-lia-text-primary">Campos do perfil enviados à IA</span>
          <span className="text-xs text-lia-text-disabled">
            {activeCount} / {totalCanonical} ativos
          </span>
        </div>

        {/* Overall progress bar */}
        <div className="h-1.5 rounded-full bg-lia-bg-tertiary overflow-hidden">
          <div
            className="h-full rounded-full bg-lia-text-secondary transition-[width] duration-300"
            style={{ width: `${(activeCount / totalCanonical) * 100}%` }}
            aria-valuenow={activeCount}
            aria-valuemax={totalCanonical}
            role="progressbar"
            aria-label={`${activeCount} de ${totalCanonical} campos ativos`}
          />
        </div>

        {/* Per-category breakdown */}
        <div className="space-y-1.5 pt-1">
          {categories.map((cat) => (
            <div key={cat.id} className="flex items-center gap-2 text-[11px]">
              <div className="w-36 text-lia-text-tertiary truncate shrink-0">{cat.label}</div>
              <div className="flex-1 h-1 rounded-full bg-lia-bg-tertiary overflow-hidden">
                <div
                  className="h-full rounded-full bg-lia-text-tertiary transition-[width] duration-300"
                  style={{
                    width:
                      cat.totalCount > 0
                        ? `${(cat.activeCount / cat.totalCount) * 100}%`
                        : "0%",
                  }}
                />
              </div>
              <div className="w-10 text-right text-lia-text-disabled shrink-0">
                {cat.activeCount}/{cat.totalCount}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Section B: Perfil da empresa ─────────────────────────────────── */}
      <div className="space-y-2">
        <span className="text-xs font-semibold text-lia-text-primary">Dados do perfil que a LIA conhece</span>
        <div className="space-y-1.5 pt-0.5">
          {profileSections.map((section) => (
            <div key={section.id} className="flex items-center gap-2 text-xs">
              <span
                className={section.isFilled ? "text-lia-text-tertiary" : "text-lia-text-disabled"}
                aria-hidden="true"
              >
                {section.isFilled ? "●" : "○"}
              </span>
              <span className={section.isFilled ? "text-lia-text-secondary" : "text-lia-text-disabled"}>
                {section.label}
              </span>
              {section.isFilled && section.detail ? (
                <span className="text-lia-text-disabled text-[10px]">{section.detail}</span>
              ) : !section.isFilled ? (
                <span className="text-lia-text-disabled italic text-[10px]">— não preenchido</span>
              ) : null}
            </div>
          ))}
        </div>
      </div>

      {/* ── Section C: Learning Loops ──────────────────────────────────── */}
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-lia-text-primary">Capacidades de aprendizado</span>
          {!masterLoopEnabled && (
            <span className="text-[10px] text-lia-text-disabled italic">(desativadas — chave mestre off)</span>
          )}
        </div>
        <div className="space-y-1.5 pt-0.5">
          {LOOP_LABELS.map(({ key, label }) => {
            const enabled = masterLoopEnabled && loopsConfig[key]
            return (
              <div key={key} className="flex items-center gap-2 text-xs">
                <span
                  className={enabled ? "text-lia-text-tertiary" : "text-lia-text-disabled"}
                  aria-hidden="true"
                >
                  {enabled ? "●" : "○"}
                </span>
                <span className={enabled ? "text-lia-text-secondary" : "text-lia-text-disabled"}>{label}</span>
                {!enabled && (
                  <span className="ml-auto text-[10px] text-lia-text-disabled shrink-0">inativo</span>
                )}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
