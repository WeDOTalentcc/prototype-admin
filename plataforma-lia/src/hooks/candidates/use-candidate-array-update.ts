"use client"

import { useState, useCallback } from "react"
import { mutate } from "swr"
import { toast } from "sonner"
import { useCurrentCompany } from "@/hooks/company/use-current-company"
import { LGPD_BLOCKED_FIELDS } from "./use-candidate-field-update"

export interface ArrayUpdateResult {
  success: boolean
  error?: string
}

/**
 * Canonical hook for updating array fields on a candidate (experiences,
 * education, skills, languages, certifications, tags).
 *
 * Backend: POST /api/backend-proxy/chat/actions/candidate-field-update
 * Strategy: sends full array as field_value (replace-all semantics).
 *
 * Multi-tenant via JWT. LGPD: refuses blocked field names runtime.
 *
 * Usage:
 *   const { updateArray, addItem, removeItem } = useCandidateArrayUpdate(
 *     candidateId,
 *     "experiences",
 *     experiences,
 *   )
 *   await updateArray((arr) => arr.map((e, i) => i === idx ? newItem : e))
 */
export function useCandidateArrayUpdate<T>(
  candidateId: string | undefined,
  fieldName: string,
  currentArray: T[]
) {
  const { companyId } = useCurrentCompany()
  const [saving, setSaving] = useState(false)

  const submit = useCallback(
    async (newArray: T[]): Promise<ArrayUpdateResult> => {
      if (!candidateId) return { success: false, error: "Candidato sem id" }
      if (LGPD_BLOCKED_FIELDS.has(fieldName.toLowerCase())) {
        return { success: false, error: `Campo '${fieldName}' é LGPD-sensível.` }
      }
      setSaving(true)
      try {
        // F6 Item 3: dedicated REST endpoints for canonical arrays.
        // Falls back to candidate-field-update for other fields.
        const dedicatedEndpoint = (
          fieldName === "work_history" ? `/api/backend-proxy/candidates/${candidateId}/experiences` :
          fieldName === "education" ? `/api/backend-proxy/candidates/${candidateId}/education` :
          fieldName === "technical_skills" ? `/api/backend-proxy/candidates/${candidateId}/skills` :
          fieldName === "certifications" ? `/api/backend-proxy/candidates/${candidateId}/certifications` :
          null
        )
        const response = dedicatedEndpoint
          ? await fetch(dedicatedEndpoint, {
              method: "PUT",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(newArray),
            })
          : await fetch("/api/backend-proxy/chat/actions/candidate-field-update", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                candidate_id: candidateId,
                fields: { [fieldName]: newArray },
              }),
            })
        if (!response.ok) {
          const errBody = (await response.json().catch(() => ({}))) as { detail?: string; error?: string; request_id?: string }
          const msg = errBody.detail ?? errBody.error ?? `Erro ${response.status} ao salvar ${fieldName}`
          const _rid = errBody.request_id ? ` (ID: ${errBody.request_id})` : ""
          toast.error("Erro ao salvar", { description: `${msg}${_rid}` })
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
        setSaving(false)
      }
    },
    [candidateId, companyId, fieldName]
  )

  const updateItem = useCallback(
    async (index: number, newItem: T): Promise<ArrayUpdateResult> => {
      const next = currentArray.map((it, i) => (i === index ? newItem : it))
      return submit(next)
    },
    [currentArray, submit]
  )

  const addItem = useCallback(
    async (newItem: T): Promise<ArrayUpdateResult> => {
      return submit([...currentArray, newItem])
    },
    [currentArray, submit]
  )

  const removeItem = useCallback(
    async (index: number): Promise<ArrayUpdateResult> => {
      const next = currentArray.filter((_, i) => i !== index)
      return submit(next)
    },
    [currentArray, submit]
  )

  return { updateItem, addItem, removeItem, saving }
}
