"use client"

/**
 * usePipelineStageTemplates — canonical hook para o catalogo dinamico per-tenant.
 *
 * Audit 2026-05-20 Sprint 2 F3: substitui o catalogo hardcoded DEFAULT_STAGES
 * (espalhado em src/components/settings/RecruitmentJourneyConfig.tsx +
 * create-job-with-candidates-modal.tsx + add-to-job-modal.tsx) por fetch
 * dinamico via API endpoints F2 (POST /api/backend-proxy/pipeline-stage-templates).
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

export type ActionBehavior =
  | "intake"
  | "screening"
  | "passive"
  | "scheduling"
  | "evaluation"
  | "verification"
  | "offer"
  | "conclusion_hired"
  | "conclusion_declined"
  | "conclusion_rejected"

export type DefaultChannel = "email" | "email_whatsapp" | "whatsapp" | "none"

export type StageCategory = "system" | "custom" | "catalog"

export type StageType = "system" | "custom" | "default"

export interface PipelineStageSubstatus {
  key: string
  label: string
  order: number
}

export interface PipelineStageData {
  label: string
  key: string
  color?: string
  icon?: string
  order: number
  is_default_in_pipeline: boolean
  action_behavior?: ActionBehavior
  default_channel?: DefaultChannel
  stage_category?: StageCategory
  type?: StageType
  sla_hours?: number
  substatuses?: PipelineStageSubstatus[]
  metadata?: Record<string, unknown>
}

export interface PipelineStageTemplate {
  id: string
  company_id: string | null
  is_master_template: boolean
  parent_template_id: string | null
  data: PipelineStageData
  created_at: string
  updated_at: string
  created_by: string | null
  deleted_at: string | null
}

export interface ListResponse {
  items: PipelineStageTemplate[]
  total: number
  master_count: number
  custom_count: number
}

interface UsePipelineStageTemplatesResult {
  templates: PipelineStageTemplate[]
  masterCount: number
  customCount: number
  total: number
  isLoading: boolean
  error: string | null
  refetch: () => Promise<void>
  createCustom: (data: PipelineStageData) => Promise<PipelineStageTemplate | null>
  updateTemplate: (
    id: string,
    data: PipelineStageData,
  ) => Promise<PipelineStageTemplate | null>
  deleteTemplate: (id: string) => Promise<boolean>
  customizeMaster: (
    masterId: string,
    overrides?: PipelineStageData,
  ) => Promise<PipelineStageTemplate | null>
}

export function usePipelineStageTemplates(
  options: { includeMaster?: boolean } = {},
): UsePipelineStageTemplatesResult {
  const { includeMaster = true } = options
  const [templates, setTemplates] = useState<PipelineStageTemplate[]>([])
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
        `/api/backend-proxy/pipeline-stage-templates?${qs}`,
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
    async (data: PipelineStageData) => {
      try {
        const res = await fetch(
          "/api/backend-proxy/pipeline-stage-templates",
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
        const created: PipelineStageTemplate = await res.json()
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
    async (id: string, data: PipelineStageData) => {
      try {
        const res = await fetch(
          `/api/backend-proxy/pipeline-stage-templates/${encodeURIComponent(id)}`,
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
        const updated: PipelineStageTemplate = await res.json()
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
          `/api/backend-proxy/pipeline-stage-templates/${encodeURIComponent(id)}`,
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
    async (masterId: string, overrides?: PipelineStageData) => {
      try {
        const res = await fetch(
          `/api/backend-proxy/pipeline-stage-templates/${encodeURIComponent(masterId)}/customize`,
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
        const custom: PipelineStageTemplate = await res.json()
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
 * Flat-shape canonical compativel com o antigo DEFAULT_STAGES (RecruitmentStage).
 * Permite migracao incremental dos consumers sem reescrever shape de props.
 *
 * server template: { id, data: { label, key, order, color, ... }, is_master_template, ... }
 * flat shape:      { id, name, display_name, order, ..., _isMaster, _serverId }
 */
export interface FlatPipelineStage {
  id: string  // serverId UUID
  name: string  // = data.key (snake_case canonical)
  display_name: string  // = data.label
  order: number
  color?: string
  icon?: string
  action_behavior?: ActionBehavior
  default_channel?: DefaultChannel
  stage_category?: StageCategory
  type?: StageType
  sla?: number  // = sla_hours / 24 (canonical conversao para "dias" do legado)
  sla_hours?: number
  is_default_in_pipeline: boolean
  substatuses?: PipelineStageSubstatus[]
  isActive: boolean
  notes: string
  _isMaster: boolean
  _serverId: string
}

export function flattenTemplate(t: PipelineStageTemplate): FlatPipelineStage {
  const d = t.data
  const slaHours = d.sla_hours ?? 0
  return {
    id: t.id,
    name: d.key,
    display_name: d.label,
    order: d.order,
    color: d.color,
    icon: d.icon,
    action_behavior: d.action_behavior,
    default_channel: d.default_channel,
    stage_category: d.stage_category,
    type: d.type,
    sla_hours: slaHours,
    sla: slaHours ? Math.round(slaHours / 24) : 0,
    is_default_in_pipeline: d.is_default_in_pipeline,
    substatuses: d.substatuses,
    isActive: true,
    notes: "",
    _isMaster: t.is_master_template,
    _serverId: t.id,
  }
}

export function flattenTemplates(items: PipelineStageTemplate[]): FlatPipelineStage[] {
  return items.map(flattenTemplate)
}
