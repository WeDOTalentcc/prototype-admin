"use client"

import { useState, useCallback } from "react"
import { mutate } from "swr"
import { useCurrentCompany } from "@/hooks/company/use-current-company"
import { toast } from "sonner"

/**
 * LGPD field policy — fields that MUST NOT be editable via this hook.
 * Sensor: check_editable_fields_not_lgpd_sensitive.py enforces at build time.
 * Runtime check below is defense-in-depth.
 */
export const LGPD_BLOCKED_FIELDS = new Set([
  "race", "raca", "racial_origin",
  "gender", "genero",
  "marital_status", "estado_civil",
  "religion", "religiao",
  "health_data", "dados_saude",
  "ethnic_origin", "origem_etnica",
  "political_opinion", "opiniao_politica",
  "sexual_orientation", "orientacao_sexual",
  "union_membership", "filiacao_sindical",
  "date_of_birth", "data_nascimento",
  "cpf", "rg", "passport",
  "id", "candidate_id", "company_id", "account_id",
  "created_at", "updated_at", "created_by",
])

export interface UpdateFieldResult {
  success: boolean
  error?: string
}

/**
 * Canonical hook for editing candidate fields inline.
 *
 * Backend: POST /api/backend-proxy/chat/actions/candidate-field-update
 * Multi-tenant: company_id flows via JWT cookie (proxy resolves).
 * Optimistic update: SWR mutate(['candidate-by-id', id]) after save.
 *
 * LGPD: refuses to update fields in LGPD_BLOCKED_FIELDS at runtime
 * (defense-in-depth — sensor blocks at build time too).
 */
export function useCandidateFieldUpdate(candidateId: string | undefined) {
  const { companyId } = useCurrentCompany()
  const [saving, setSaving] = useState<Record<string, boolean>>({})

  const updateField = useCallback(
    async (fieldName: string, fieldValue: string | number | null): Promise<UpdateFieldResult> => {
      if (!candidateId) {
        return { success: false, error: "Candidato sem id" }
      }
      if (LGPD_BLOCKED_FIELDS.has(fieldName.toLowerCase())) {
        return { success: false, error: `Campo '${fieldName}' é LGPD-sensível e não pode ser editado.` }
      }

      setSaving((s) => ({ ...s, [fieldName]: true }))
      try {
        // F9 Item 1: name field uses dedicated /identity endpoint (encryption-aware via ORM)
        const dedicatedEndpoint = fieldName === "name"
          ? `/api/backend-proxy/candidates/${candidateId}/identity`
          : null
        const response = dedicatedEndpoint
          ? await fetch(dedicatedEndpoint, {
              method: "PUT",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ [fieldName]: fieldValue }),
            })
          : await fetch("/api/backend-proxy/chat/actions/candidate-field-update", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                candidate_id: candidateId,
                fields: { [fieldName]: fieldValue },
              }),
            })

        if (!response.ok) {
          const errBody = await response.json().catch(() => ({}))
          const _ebody = errBody as { detail?: string; error?: string; request_id?: string }
          const msg = _ebody.detail ?? _ebody.error ?? `Erro ${response.status} ao salvar ${fieldName}`
          const _rid = _ebody.request_id ? ` (ID: ${_ebody.request_id})` : ""
          toast.error("Erro ao salvar", { description: `${msg}${_rid}` })
          return { success: false, error: msg }
        }

        const data = (await response.json()) as { success?: boolean; updated_count?: number }
        if (data.success === false) {
          const msg = `Backend recusou atualização de ${fieldName}`
          toast.error("Erro ao salvar", { description: msg })
          return { success: false, error: msg }
        }

        if (companyId) {
          await mutate(["candidate-by-id", candidateId])
        }
        toast.success("Salvo", { description: `${fieldName} atualizado` })
        return { success: true }
      } catch (err) {
        const msg = err instanceof Error ? err.message : "Erro desconhecido"
        toast.error("Erro ao salvar", { description: msg })
        return { success: false, error: msg }
      } finally {
        setSaving((s) => ({ ...s, [fieldName]: false }))
      }
    },
    [candidateId, companyId]
  )

  const isSaving = useCallback((fieldName: string) => Boolean(saving[fieldName]), [saving])

  return { updateField, isSaving, saving }
}
