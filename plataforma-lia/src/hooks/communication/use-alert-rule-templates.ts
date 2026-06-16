"use client"

/**
 * useAlertRuleTemplates — canonical hook para o catalogo dinamico per-tenant.
 *
 * Audit 2026-05-20 Sprint 3 F4: substitui o catalogo hardcoded
 * `DEFAULT_ALERTS` em `CommunicationHub.constants.ts` por fetch dinamico
 * via API endpoints F2 (POST /api/backend-proxy/alert-rule-templates).
 *
 * Decisoes Paulo 2026-05-20:
 * - A1: customize cria copia total no DB (nao override por field)
 * - B1: customize e snapshot canonical (nao sincroniza com master apos)
 * - C: admin tudo, recrutador create-novos OK mas nao delete/update-de-outros
 *
 * Pattern canonical: useState + fetch direto (sem React Query — projeto nao
 * usa). Cache em-memory + invalidate manual via refetch().
 */

import { useCallback, useEffect, useState } from "react"

export type AlertAudience = "recruiter" | "admin" | "candidate"
export type AlertChannel = "email" | "in_app" | "teams" | "whatsapp"

export interface AlertRuleData {
  event_type: string
  label: string
  description?: string
  audience: AlertAudience
  channels: AlertChannel[]
  delay_minutes: number
  schedule_lgpd_compliant: boolean
  rationale?: string
  enabled_default?: boolean
  legacy_id?: string
}

export interface AlertRuleTemplate {
  id: string
  company_id: string | null
  is_master_template: boolean
  parent_template_id: string | null
  data: AlertRuleData
  created_at: string
  updated_at: string
  created_by: string | null
  deleted_at: string | null
}

export interface ListResponse {
  items: AlertRuleTemplate[]
  total: number
  master_count: number
  custom_count: number
}

interface UseAlertRuleTemplatesResult {
  templates: AlertRuleTemplate[]
  masterCount: number
  customCount: number
  total: number
  isLoading: boolean
  error: string | null
  refetch: () => Promise<void>
  createCustom: (data: AlertRuleData) => Promise<AlertRuleTemplate | null>
  updateTemplate: (
    id: string,
    data: AlertRuleData,
  ) => Promise<AlertRuleTemplate | null>
  deleteTemplate: (id: string) => Promise<boolean>
  customizeMaster: (
    masterId: string,
    overrides?: AlertRuleData,
  ) => Promise<AlertRuleTemplate | null>
}

export function useAlertRuleTemplates(
  options: { includeMaster?: boolean } = {},
): UseAlertRuleTemplatesResult {
  const { includeMaster = true } = options
  const [templates, setTemplates] = useState<AlertRuleTemplate[]>([])
  const [masterCount, setMasterCount] = useState(0)
  const [customCount, setCustomCount] = useState(0)
  const [total, setTotal] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchAll = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const qs = new URLSearchParams({
        include_master: String(includeMaster),
      }).toString()
      const res = await fetch(
        `/api/backend-proxy/alert-rule-templates?${qs}`,
      )
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`)
      }
      const data: ListResponse = await res.json()
      setTemplates(data.items || [])
      setMasterCount(data.master_count ?? 0)
      setCustomCount(data.custom_count ?? 0)
      setTotal(data.total ?? 0)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao carregar templates")
    } finally {
      setIsLoading(false)
    }
  }, [includeMaster])

  useEffect(() => {
    fetchAll()
  }, [fetchAll])

  const createCustom = useCallback(
    async (data: AlertRuleData) => {
      try {
        const res = await fetch(
          "/api/backend-proxy/alert-rule-templates",
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ data }),
          },
        )
        if (!res.ok) {
          const err = await res.json().catch(() => ({}))
          throw new Error(err.detail || err.error || `HTTP ${res.status}`)
        }
        const created: AlertRuleTemplate = await res.json()
        await fetchAll()
        return created
      } catch (e) {
        setError(e instanceof Error ? e.message : "Erro ao criar template")
        return null
      }
    },
    [fetchAll],
  )

  const updateTemplate = useCallback(
    async (id: string, data: AlertRuleData) => {
      try {
        const res = await fetch(
          `/api/backend-proxy/alert-rule-templates/${encodeURIComponent(id)}`,
          {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ data }),
          },
        )
        if (!res.ok) {
          const err = await res.json().catch(() => ({}))
          throw new Error(err.detail || err.error || `HTTP ${res.status}`)
        }
        const updated: AlertRuleTemplate = await res.json()
        await fetchAll()
        return updated
      } catch (e) {
        setError(e instanceof Error ? e.message : "Erro ao atualizar template")
        return null
      }
    },
    [fetchAll],
  )

  const deleteTemplate = useCallback(
    async (id: string) => {
      try {
        const res = await fetch(
          `/api/backend-proxy/alert-rule-templates/${encodeURIComponent(id)}`,
          { method: "DELETE" },
        )
        if (!res.ok && res.status !== 204) {
          const err = await res.json().catch(() => ({}))
          throw new Error(err.detail || err.error || `HTTP ${res.status}`)
        }
        await fetchAll()
        return true
      } catch (e) {
        setError(e instanceof Error ? e.message : "Erro ao deletar template")
        return false
      }
    },
    [fetchAll],
  )

  const customizeMaster = useCallback(
    async (masterId: string, overrides?: AlertRuleData) => {
      try {
        const res = await fetch(
          `/api/backend-proxy/alert-rule-templates/${encodeURIComponent(masterId)}/customize`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(overrides ? { overrides } : {}),
          },
        )
        if (!res.ok) {
          const err = await res.json().catch(() => ({}))
          throw new Error(err.detail || err.error || `HTTP ${res.status}`)
        }
        const custom: AlertRuleTemplate = await res.json()
        await fetchAll()
        return custom
      } catch (e) {
        setError(e instanceof Error ? e.message : "Erro ao customizar master")
        return null
      }
    },
    [fetchAll],
  )

  return {
    templates,
    masterCount,
    customCount,
    total,
    isLoading,
    error,
    refetch: fetchAll,
    createCustom,
    updateTemplate,
    deleteTemplate,
    customizeMaster,
  }
}


/**
 * Flat-shape canonical compativel com o antigo DEFAULT_ALERTS (AlertConfig).
 * Permite migracao incremental de componentes consumindo o catalogo
 * hardcoded sem reescrever shape de props.
 *
 * server template: { id, data: { event_type, label, channels[], ... }, is_master_template, ... }
 * legacy shape:    { id, name, description, enabled, channel: 'email'|'teams'|'both' }
 *
 * Mapeamento channels[] -> channel singular para legacy AlertConfig:
 *   ['email', 'in_app']        -> 'both'
 *   ['email']                  -> 'email'
 *   ['teams']                  -> 'teams'
 *   ['email', 'teams', ...]    -> 'both'
 *   default                    -> 'email'
 */
export interface FlatAlertConfig {
  id: string  // serverId UUID
  name: string  // = data.label
  description: string
  enabled: boolean
  channel: "email" | "teams" | "both"
  // canonical fields preserved for migration callers
  event_type: string
  audience: AlertAudience
  channels: AlertChannel[]
  delay_minutes: number
  schedule_lgpd_compliant: boolean
  rationale?: string
  _isMaster: boolean
  _serverId: string
  _legacyId?: string
}

function channelsToLegacy(channels: AlertChannel[]): "email" | "teams" | "both" {
  const set = new Set(channels)
  const hasEmail = set.has("email") || set.has("in_app")
  const hasTeams = set.has("teams")
  if (hasEmail && hasTeams) return "both"
  if (hasTeams) return "teams"
  if (hasEmail) return "email"
  return "email"
}

export function flattenTemplate(t: AlertRuleTemplate): FlatAlertConfig {
  const d = t.data
  return {
    id: t.id,
    name: d.label,
    description: d.description || "",
    enabled: d.enabled_default ?? true,
    channel: channelsToLegacy(d.channels || []),
    event_type: d.event_type,
    audience: d.audience,
    channels: d.channels,
    delay_minutes: d.delay_minutes,
    schedule_lgpd_compliant: d.schedule_lgpd_compliant,
    rationale: d.rationale,
    _isMaster: t.is_master_template,
    _serverId: t.id,
    _legacyId: d.legacy_id,
  }
}

export function flattenTemplates(items: AlertRuleTemplate[]): FlatAlertConfig[] {
  return items.map(flattenTemplate)
}
