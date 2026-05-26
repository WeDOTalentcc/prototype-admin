"use client"

import { useCallback } from "react"
import useSWR from "swr"

export interface PipelineStage {
  name: string
  order: number
  type: "automatic" | "manual" | "hybrid" | string
  sla_days: number
  instructions?: string
}

/**
 * Full backend PipelineTemplate shape (broader than the lightweight
 * `PipelineTemplate` exposed in edit-job.types.ts which only models what
 * the wizard needs at apply-time).
 */
export interface PipelineTemplateFull {
  id: string
  company_id: string
  name: string
  description: string | null
  stages: PipelineStage[]
  is_default: boolean
  is_active: boolean
  is_archived?: boolean
  usage_count: number
  department_hint?: string[]
  seniority_hint?: string[]
  job_family_hint?: string[]
  created_by?: string | null
  updated_by?: string | null
  created_at?: string
  updated_at?: string
}

interface ListResponse {
  templates?: PipelineTemplateFull[]
  items?: PipelineTemplateFull[]
  total?: number
}

export interface CreateOrUpdateTemplatePayload {
  name: string
  description?: string | null
  stages: PipelineStage[]
  is_default?: boolean
  is_active?: boolean
  department_hint?: string[]
  seniority_hint?: string[]
  job_family_hint?: string[]
}

const BASE = "/api/backend-proxy/company/pipeline-templates"

async function fetcher<T>(url: string): Promise<T> {
  const res = await fetch(url, { credentials: "include" })
  if (!res.ok) {
    const text = await res.text().catch(() => "")
    throw new Error(`HTTP ${res.status}: ${text || res.statusText}`)
  }
  return res.json() as Promise<T>
}

async function jsonRequest<T>(url: string, method: string, body?: unknown): Promise<T> {
  const res = await fetch(url, {
    method,
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    credentials: "include",
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) {
    const text = await res.text().catch(() => "")
    throw new Error(`HTTP ${res.status}: ${text || res.statusText}`)
  }
  // 204 No Content
  if (res.status === 204) return undefined as unknown as T
  return res.json() as Promise<T>
}

export function usePipelineTemplates() {
  const { data, error, isLoading, mutate } = useSWR<ListResponse | PipelineTemplateFull[]>(
    BASE + "/",
    fetcher
  )

  const templates: PipelineTemplateFull[] = Array.isArray(data)
    ? data
    : (data?.templates ?? data?.items ?? [])
  const total: number = Array.isArray(data) ? data.length : (data?.total ?? templates.length)

  const createTemplate = useCallback(
    async (payload: CreateOrUpdateTemplatePayload): Promise<PipelineTemplateFull | null> => {
      try {
        const created = await jsonRequest<PipelineTemplateFull>(BASE + "/", "POST", payload)
        await mutate()
        return created
      } catch (err) {
        console.error("[pipeline-templates] create failed", err)
        return null
      }
    },
    [mutate]
  )

  const updateTemplate = useCallback(
    async (id: string, payload: CreateOrUpdateTemplatePayload): Promise<PipelineTemplateFull | null> => {
      try {
        const updated = await jsonRequest<PipelineTemplateFull>(BASE + "/" + id, "PUT", payload)
        await mutate()
        return updated
      } catch (err) {
        console.error("[pipeline-templates] update failed", err)
        return null
      }
    },
    [mutate]
  )

  const cloneTemplate = useCallback(
    async (id: string, newName?: string): Promise<PipelineTemplateFull | null> => {
      try {
        const url = BASE + "/" + id + "/clone" + (newName ? "?new_name=" + encodeURIComponent(newName) : "")
        const cloned = await jsonRequest<PipelineTemplateFull>(url, "POST")
        await mutate()
        return cloned
      } catch (err) {
        console.error("[pipeline-templates] clone failed", err)
        return null
      }
    },
    [mutate]
  )

  const archiveTemplate = useCallback(
    async (id: string): Promise<boolean> => {
      try {
        await jsonRequest<unknown>(BASE + "/" + id + "/archive", "POST")
        await mutate()
        return true
      } catch (err) {
        console.error("[pipeline-templates] archive failed", err)
        return false
      }
    },
    [mutate]
  )

  const deleteTemplate = useCallback(
    async (id: string): Promise<boolean> => {
      try {
        await jsonRequest<unknown>(BASE + "/" + id, "DELETE")
        await mutate()
        return true
      } catch (err) {
        console.error("[pipeline-templates] delete failed", err)
        return false
      }
    },
    [mutate]
  )

  const seedDefaults = useCallback(
    async (force?: boolean): Promise<boolean> => {
      try {
        const url = BASE + "/seed-defaults" + (force ? "?force=true" : "")
        await jsonRequest<unknown>(url, "POST")
        await mutate()
        return true
      } catch (err) {
        console.error("[pipeline-templates] seed defaults failed", err)
        return false
      }
    },
    [mutate]
  )

  return {
    templates,
    total,
    isLoading,
    error,
    mutate,
    createTemplate,
    updateTemplate,
    cloneTemplate,
    archiveTemplate,
    deleteTemplate,
    seedDefaults,
  }
}
