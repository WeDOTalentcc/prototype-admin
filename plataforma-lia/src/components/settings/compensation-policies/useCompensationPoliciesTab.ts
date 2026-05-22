"use client"

import { useCallback, useEffect, useState } from "react"
import { useCompanyId } from "@/hooks/company/useCompanyId"
import type { CompensationPolicyRecord } from "./compensation-policies-types"
import { defaultPolicy } from "./compensation-policies-types"
import { apiFetch } from "@/lib/api/api-fetch"

const toStringArray = (raw: unknown, fallback: string[] = []): string[] => {
  if (Array.isArray(raw)) return raw.map((x) => String(x))
  if (raw === undefined || raw === null) return fallback
  return [String(raw)]
}

const normalizePolicy = (p: Record<string, unknown>): CompensationPolicyRecord => ({
  id: typeof p.id === "string" ? p.id : undefined,
  name: String(p.name || ""),
  description: String(p.description || ""),
  policy_type: String(p.policy_type || "mixed"),
  currency: String(p.currency || "BRL"),

  salary_bands: Array.isArray(p.salary_bands) ? p.salary_bands as CompensationPolicyRecord["salary_bands"] : [],
  bonus_structure: (p.bonus_structure && typeof p.bonus_structure === "object" && !Array.isArray(p.bonus_structure)) ? p.bonus_structure as Record<string, unknown> : {},
  equity_rules: (p.equity_rules && typeof p.equity_rules === "object" && !Array.isArray(p.equity_rules)) ? p.equity_rules as Record<string, unknown> : {},
  benefits_package: (p.benefits_package && typeof p.benefits_package === "object" && !Array.isArray(p.benefits_package)) ? p.benefits_package as Record<string, unknown> : {},
  variable_compensation: (p.variable_compensation && typeof p.variable_compensation === "object")
    ? { items: Array.isArray((p.variable_compensation as Record<string, unknown>).items) ? (p.variable_compensation as Record<string, unknown>).items as CompensationPolicyRecord["variable_compensation"]["items"] : [] }
    : { items: [] },

  applicable_departments: toStringArray(p.applicable_departments),
  applicable_seniority: toStringArray(p.applicable_seniority),
  applicable_roles: toStringArray(p.applicable_roles),

  is_active: Boolean(p.is_active ?? true),
  is_default: Boolean(p.is_default ?? false),

  effective_from: typeof p.effective_from === "string" ? p.effective_from : undefined,
  effective_until: typeof p.effective_until === "string" ? p.effective_until : undefined,
  approved_by: typeof p.approved_by === "string" ? p.approved_by : undefined,
  approved_at: typeof p.approved_at === "string" ? p.approved_at : undefined,

  version: typeof p.version === "number" ? p.version : 1,
  revision_history: Array.isArray(p.revision_history) ? p.revision_history as Array<Record<string, unknown>> : [],
  created_by: typeof p.created_by === "string" ? p.created_by : undefined,
  updated_by: typeof p.updated_by === "string" ? p.updated_by : undefined,
  created_at: typeof p.created_at === "string" ? p.created_at : undefined,
  updated_at: typeof p.updated_at === "string" ? p.updated_at : undefined,
})

export function useCompensationPoliciesTab() {
  const { companyId } = useCompanyId()
  const [policies, setPolicies] = useState<CompensationPolicyRecord[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [showModal, setShowModal] = useState(false)
  const [editingPolicy, setEditingPolicy] = useState<CompensationPolicyRecord | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const fetchPolicies = useCallback(async () => {
    if (!companyId) return
    setIsLoading(true)
    try {
      const res = await apiFetch(
        `/api/backend-proxy/company/compensation-policies?company_id=${companyId}`
      )
      const data: unknown[] = Array.isArray(res) ? res : []
      setPolicies(data.map((p) => normalizePolicy(p as Record<string, unknown>)))
    } catch (err) {
      console.error("Error loading compensation policies:", err)
      setError("Erro ao carregar políticas de remuneração")
    } finally {
      setIsLoading(false)
    }
  }, [companyId])

  useEffect(() => {
    fetchPolicies()
  }, [fetchPolicies])

  const openCreate = useCallback(() => {
    setEditingPolicy({ ...defaultPolicy })
    setShowModal(true)
  }, [])

  const openEdit = useCallback((policy: CompensationPolicyRecord) => {
    setEditingPolicy({ ...policy })
    setShowModal(true)
  }, [])

  const closeModal = useCallback(() => {
    setShowModal(false)
    setEditingPolicy(null)
    setError(null)
  }, [])

  const savePolicy = useCallback(
    async (data: CompensationPolicyRecord) => {
      if (!companyId) return
      setIsSaving(true)
      setError(null)
      try {
        const isEdit = Boolean(data.id)
        const url = isEdit
          ? `/api/backend-proxy/company/compensation-policies/${data.id}`
          : `/api/backend-proxy/company/compensation-policies`
        const method = isEdit ? "PUT" : "POST"

        const payload = { ...data, company_id: companyId }
        delete (payload as Record<string, unknown>).id

        const response = await apiFetch(url, {
          method,
          body: JSON.stringify(payload),
        })
        const result = (await response.json()) as Record<string, unknown>

        const normalized = normalizePolicy(result)
        if (isEdit) {
          setPolicies((prev) =>
            prev.map((p) => (p.id === normalized.id ? normalized : p))
          )
          setSuccessMessage(`Política "${normalized.name}" atualizada (v${normalized.version})`)
        } else {
          setPolicies((prev) => [...prev, normalized])
          setSuccessMessage(`Política "${normalized.name}" criada`)
        }
        closeModal()
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : "Erro ao salvar política"
        setError(msg)
      } finally {
        setIsSaving(false)
        setTimeout(() => setSuccessMessage(null), 4000)
      }
    },
    [companyId, closeModal]
  )

  const deactivatePolicy = useCallback(
    async (policy: CompensationPolicyRecord) => {
      if (!policy.id) return
      try {
        await apiFetch(
          `/api/backend-proxy/company/compensation-policies/${policy.id}`,
          { method: "DELETE" }
        )
        setPolicies((prev) =>
          prev.map((p) =>
            p.id === policy.id ? { ...p, is_active: false } : p
          )
        )
        setSuccessMessage(`Política "${policy.name}" desativada`)
        setTimeout(() => setSuccessMessage(null), 3000)
      } catch (err) {
        console.error("Error deactivating policy:", err)
        setError("Erro ao desativar política")
      }
    },
    []
  )

  const seedDefaults = useCallback(async () => {
    if (!companyId) return
    setIsSaving(true)
    try {
      await apiFetch(
        `/api/backend-proxy/company/compensation-policies/seed-defaults?company_id=${companyId}`,
        { method: "POST" }
      )
      await fetchPolicies()
      setSuccessMessage("Políticas padrão criadas com sucesso")
      setTimeout(() => setSuccessMessage(null), 4000)
    } catch (err) {
      console.error("Error seeding defaults:", err)
      setError("Erro ao criar políticas padrão")
    } finally {
      setIsSaving(false)
    }
  }, [companyId, fetchPolicies])

  return {
    policies,
    isLoading,
    isSaving,
    showModal,
    editingPolicy,
    successMessage,
    error,
    openCreate,
    openEdit,
    closeModal,
    savePolicy,
    deactivatePolicy,
    seedDefaults,
    refetch: fetchPolicies,
  }
}
