/**
 * useFieldSave.ts — React Query mutation hook para salvar campos (Sprint 2.2, 2026-05-26)
 *
 * Extraído de use-company-settings-cards.ts. Responsabilidade única:
 * persistir edições inline de campo em seus endpoints canônicos e
 * invalidar as queries afetadas via React Query.
 *
 * Endpoints:
 * - basic    → PUT  /api/backend-proxy/company/profile/{id}
 * - culture  → PUT  /api/backend-proxy/company/culture-profile/{id}
 * - tech     → POST /api/backend-proxy/skills-catalog/company/skills-catalog/sync
 *              | PUT /culture-profile (engineering_culture, default_languages)
 * - policy   → PATCH /api/backend-proxy/hiring-policy/block
 * - benefits → (não editável inline — usa BenefitsListSection)
 * - workforce→ (não editável inline — usa WorkforceHubContent)
 * - documents→ PUT /api/backend-proxy/company/profile/{id} additional_data
 */

"use client"

import { useMutation, useQueryClient } from "@tanstack/react-query"
import { SETTINGS_QUERY_KEYS, dispatchSettingsUpdate } from "@/hooks/settings/useSettingsBroadcast"
import { POLICY_FIELD_TO_BLOCK } from "@/hooks/settings/useCompanyBlocks"
import type { CompanyData } from "@/hooks/settings/department-types"

// ─── Types ───────────────────────────────────────────────────────────────────

export interface SaveFieldArgs {
  block: string
  field: string
  value: unknown
  companyId: string
  companyData: CompanyData | null
}

// ─── Error extraction ────────────────────────────────────────────────────────

export async function extractErrorMessage(response: Response, fallback: string): Promise<string> {
  try {
    const data = await response.json()
    if (data?.detail) {
      return typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail)
    }
    if (data?.message && typeof data.message === "string") return data.message
    if (data?.error && typeof data.error === "string") return data.error
  } catch {
    /* not JSON */
  }
  if (response.status === 401 || response.status === 403) {
    return "Sessao expirada ou sem permissao. Recarregue a pagina."
  }
  if (response.status >= 500) {
    return "Backend indisponivel. Tente novamente em instantes."
  }
  return fallback
}

// ─── Per-block save dispatchers ───────────────────────────────────────────────

async function saveBasicField(companyId: string, field: string, value: unknown): Promise<Response> {
  const fieldMap: Record<string, string> = {
    name: "name",
    tradeName: "trading_name",
    cnpj: "cnpj",
    website: "website",
    industry: "industry",
    size: "company_size",
    employee_count: "employee_count",
    email: "hr_email",
    phone: "hr_phone",
    founded_year: "founded_year",
    headquarters: "headquarters_city",
    linkedin_url: "linkedin_url",
  }
  const apiField = fieldMap[field] || field
  let payload: Record<string, unknown> = { [apiField]: value }
  if (field === "headquarters" && typeof value === "string") {
    const trimmed = value.trim()
    const lastComma = trimmed.lastIndexOf(",")
    if (lastComma === -1) {
      payload = { headquarters_city: trimmed }
    } else {
      const city = trimmed.slice(0, lastComma).trim()
      const state = trimmed.slice(lastComma + 1).trim()
      payload = { headquarters_city: city, headquarters_state: state }
    }
  }
  return fetch(`/api/backend-proxy/company/profile/${companyId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
}

async function saveCultureOrTechProfileField(companyId: string, field: string, value: unknown): Promise<Response> {
  const cultureFieldMap: Record<string, string> = {
    mission: "mission", vision: "vision", values: "values",
    work_model: "work_model", dei_initiatives: "dei_initiatives",
    sustainability: "sustainability", social_impact: "social_impact",
    leadership_style: "leadership_style", growth_opportunities: "growth_opportunities",
    team_dynamics: "team_dynamics", evp_bullets: "evp_bullets",
    engineering_culture: "engineering_culture", default_languages: "default_languages",
  }
  const apiField = cultureFieldMap[field] || field
  return fetch(`/api/backend-proxy/company/culture-profile/${encodeURIComponent(companyId)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ [apiField]: value }),
  })
}

async function saveTechStackField(value: unknown): Promise<Response> {
  const skills = Array.isArray(value)
    ? (value as unknown[]).map((s) => String(s).trim()).filter(Boolean)
    : typeof value === "string"
      ? value.split(",").map((s) => s.trim()).filter(Boolean)
      : []
  return fetch("/api/backend-proxy/skills-catalog/company/skills-catalog/sync", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tech_stack: skills }),
  })
}

async function savePolicyField(field: string, value: unknown): Promise<Response> {
  const subBlock = POLICY_FIELD_TO_BLOCK[field]
  if (!subBlock) throw new Error(`Campo de política não suportado para edição manual: ${field}`)
  let parsedValue: unknown = value
  if (field === "allowed_hours" && typeof value === "string") {
    const m = value.match(/^\s*(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})\s*$/)
    if (!m) throw new Error("Horário inválido. Use o formato HH:MM - HH:MM (ex.: 09:00 - 18:00).")
    parsedValue = { start: m[1], end: m[2] }
  }
  return fetch("/api/backend-proxy/hiring-policy/block", {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ block: subBlock, data: { [field]: parsedValue } }),
  })
}

async function saveDocumentsField(
  companyId: string,
  field: string,
  value: unknown,
  companyData: CompanyData | null,
): Promise<Response> {
  const currentAdditional = ((companyData?.additional_data || {}) as Record<string, unknown>)
  const nextAdditional = { ...currentAdditional, [field]: value }
  return fetch(`/api/backend-proxy/company/profile/${companyId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ additional_data: nextAdditional }),
  })
}

// ─── Main mutation function ───────────────────────────────────────────────────

async function performSaveField({ block, field, value, companyId, companyData }: SaveFieldArgs): Promise<void> {
  let response: Response | null = null
  let fallbackErr = "Falha ao salvar campo"

  if (block === "basic") {
    response = await saveBasicField(companyId, field, value)
  } else if (block === "culture") {
    response = await saveCultureOrTechProfileField(companyId, field, value)
  } else if (block === "tech") {
    if (field === "tech_stack") {
      fallbackErr = "Falha ao salvar stack tecnológica"
      response = await saveTechStackField(value)
    } else {
      response = await saveCultureOrTechProfileField(companyId, field, value)
    }
  } else if (block === "policy") {
    fallbackErr = "Falha ao salvar política"
    response = await savePolicyField(field, value)
  } else if (block === "documents") {
    fallbackErr = "Falha ao salvar campo de remuneração / onboarding"
    response = await saveDocumentsField(companyId, field, value, companyData)
  } else if (block === "workforce") {
    throw new Error(
      "Edite o planejamento de workforce usando a tabela embutida no card (Workforce Planning).",
    )
  } else if (block === "benefits") {
    throw new Error(
      "Use a lista de benefícios abaixo (botão + Adicionar benefício) para criar ou editar itens.",
    )
  } else {
    throw new Error(`Bloco desconhecido: ${block}`)
  }

  if (response && !response.ok) {
    const message = await extractErrorMessage(response, fallbackErr)
    throw new Error(message)
  }
}

// ─── React Query mutation hook ────────────────────────────────────────────────

export interface UseFieldSaveReturn {
  saveField: (args: SaveFieldArgs) => Promise<void>
  isSavingField: boolean
}

/**
 * React Query mutation hook for inline field saves.
 *
 * On success:
 * 1. Dispatches lia:settings-updated + lia:settings-success events (chat bridge).
 * 2. Invalidates all settings queries (React Query refetches fresh data).
 *
 * Replaces: loadAll() after save + lastSelfDispatchRef dedup hack.
 * Consumers: use-company-settings-cards.ts (thin wrapper).
 */
export function useFieldSave(): UseFieldSaveReturn {
  const queryClient = useQueryClient()

  const mutation = useMutation({
    mutationFn: performSaveField,
    onSuccess: (_, { block, field, value }) => {
      // Dispatch canonical events for chat bridge + OnboardingActionOrchestrator.
      const blockToSection: Record<string, { section: string; actionId: string }> = {
        basic: { section: "profile", actionId: "configure_profile" },
        culture: { section: "culture", actionId: "configure_culture" },
        tech: { section: "tech_stack", actionId: "configure_tech_stack" },
        policy: { section: "hiring_policies", actionId: "configure_culture" },
        workforce: { section: "workforce", actionId: "configure_workforce" },
        documents: { section: "profile", actionId: "configure_profile" },
        benefits: { section: "benefits", actionId: "configure_benefits" },
      }
      const mapping = blockToSection[block]
      if (mapping) {
        dispatchSettingsUpdate({ ...mapping, field, value, source: "ui", ts: Date.now() })
      }

      // Invalidate all settings queries — triggers React Query refetch.
      // No need for lastSelfDispatchRef: useSettingsBroadcast skips source="ui".
      queryClient.invalidateQueries({ queryKey: SETTINGS_QUERY_KEYS.companyProfile() })
      queryClient.invalidateQueries({ queryKey: SETTINGS_QUERY_KEYS.hiringPolicy() })
      queryClient.invalidateQueries({ queryKey: SETTINGS_QUERY_KEYS.settingsProgress() })
      queryClient.invalidateQueries({ queryKey: ["culture-profile"] })
      queryClient.invalidateQueries({ queryKey: ["company-benefits"] })
    },
  })

  const saveField = async (args: SaveFieldArgs): Promise<void> => {
    await mutation.mutateAsync(args)
  }

  return {
    saveField,
    isSavingField: mutation.isPending,
  }
}
