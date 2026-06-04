"use client"

/**
 * useLiaFieldTogglesForSection — Fase 4 MVP (colocation).
 *
 * Expõe, para um subconjunto de campos LIA (os de um hub de origem), o estado
 * toggle on/off + instrução custom + savers, prontos para o ConfigurableFieldCard.
 * Permite que cada hub (MinhaEmpresa, Benefits, Pipeline, Screening, Workforce)
 * renderize o controle AO LADO do dado, em vez do painel-espelho central.
 *
 * Contrato canonical (idêntico ao LiaFieldsConfigPanel):
 *   GET/PUT /api/backend-proxy/company/{companyId}/field-toggles
 *   body PUT: { toggles: Record<key,bool>, comments: Record<key,str> } (mapas completos)
 *
 * React Query (REGRA settings canonical) + dispatchSettingsUpdate em cada save.
 * NB: query key local namespaced — folding em SETTINGS_QUERY_KEYS quando a
 * migração dos hubs tocar useSettingsBroadcast.
 */

import { useMemo } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { apiFetch } from "@/lib/api/api-fetch"
import { useCompanyId } from "@/hooks/company/useCompanyId"
import { dispatchSettingsUpdate } from "@/hooks/settings/useSettingsBroadcast"
import {
  LIA_FIELD_DEFINITIONS,
  type LiaFieldKey,
} from "@/hooks/company/use-company-lia-instructions"

export interface FieldTogglesState {
  toggles: Record<string, boolean>
  comments: Record<string, string>
}

export const liaFieldTogglesKey = (companyId: string | null | undefined) =>
  ["lia-field-toggles", companyId ?? "none"] as const

async function fetchFieldToggles(companyId: string): Promise<FieldTogglesState> {
  const res = await apiFetch(
    `/api/backend-proxy/company/${encodeURIComponent(companyId)}/field-toggles`,
  )
  if (!res.ok) {
    if (res.status === 404 || res.status === 422) return { toggles: {}, comments: {} }
    throw new Error(`Falha ao carregar field-toggles: ${res.status}`)
  }
  const data = await res.json()
  // Backend canonical: data.toggles (Record<string,bool>) + data.comments (Record<string,str|null>)
  const comments: Record<string, string> = {}
  for (const [k, v] of Object.entries((data?.comments ?? {}) as Record<string, unknown>)) {
    if (typeof v === "string" && v.trim()) comments[k] = v
  }
  return {
    toggles: (data?.toggles ?? {}) as Record<string, boolean>,
    comments,
  }
}

/** Props prontas para o ConfigurableFieldCard de cada campo da seção. */
export interface SectionFieldCard {
  key: LiaFieldKey
  label: string
  hint: string
  isActive: boolean
  instruction: string
  isSaving: boolean
  onToggleChange: (active: boolean) => void
  onInstructionSave: (text: string) => void
}

export interface UseLiaFieldTogglesForSectionResult {
  fields: SectionFieldCard[]
  isLoading: boolean
  error: string | null
}

interface SavePayload {
  next: FieldTogglesState
  field: string
}

export function useLiaFieldTogglesForSection(
  sectionKeys: LiaFieldKey[],
): UseLiaFieldTogglesForSectionResult {
  const { companyId, isLoading: isLoadingCompany } = useCompanyId()
  const queryClient = useQueryClient()

  const query = useQuery({
    queryKey: liaFieldTogglesKey(companyId),
    queryFn: () => fetchFieldToggles(companyId as string),
    enabled: !!companyId,
    staleTime: 30_000,
  })

  const state: FieldTogglesState = useMemo(
    () => query.data ?? { toggles: {}, comments: {} },
    [query.data],
  )

  const mutation = useMutation({
    mutationFn: async ({ next }: SavePayload) => {
      if (!companyId) throw new Error("companyId ausente")
      const res = await apiFetch(
        `/api/backend-proxy/company/${encodeURIComponent(companyId)}/field-toggles`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ toggles: next.toggles, comments: next.comments }),
        },
      )
      if (!res.ok) throw new Error(`Falha ao salvar field-toggles: ${res.status}`)
      return next
    },
    onMutate: async ({ next }: SavePayload) => {
      const key = liaFieldTogglesKey(companyId)
      await queryClient.cancelQueries({ queryKey: key })
      const prev = queryClient.getQueryData<FieldTogglesState>(key)
      queryClient.setQueryData(key, next)
      return { prev }
    },
    onError: (_err, _vars, ctx) => {
      if (ctx?.prev) queryClient.setQueryData(liaFieldTogglesKey(companyId), ctx.prev)
    },
    onSuccess: (_data, { field }: SavePayload) => {
      dispatchSettingsUpdate({
        actionId: "save_lia_field_toggle",
        section: "lia_personalizacao",
        field,
        source: "ui",
        ts: Date.now(),
      })
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: liaFieldTogglesKey(companyId) })
    },
  })

  const { mutate, isPending } = mutation

  const fields = useMemo<SectionFieldCard[]>(() => {
    return sectionKeys.map((key) => {
      const def = LIA_FIELD_DEFINITIONS[key] as { label: string; location: string } | undefined
      return {
        key,
        label: def?.label ?? key,
        hint: def?.location ?? "",
        isActive: state.toggles[key] !== false, // default ON quando ausente
        instruction: state.comments[key] ?? "",
        isSaving: isPending,
        onToggleChange: (active: boolean) =>
          mutate({
            next: { toggles: { ...state.toggles, [key]: active }, comments: state.comments },
            field: key,
          }),
        onInstructionSave: (text: string) =>
          mutate({
            next: { toggles: state.toggles, comments: { ...state.comments, [key]: text } },
            field: key,
          }),
      }
    })
  }, [sectionKeys, state, mutate, isPending])

  return {
    fields,
    isLoading: isLoadingCompany || query.isLoading,
    error: query.error ? (query.error as Error).message : null,
  }
}
