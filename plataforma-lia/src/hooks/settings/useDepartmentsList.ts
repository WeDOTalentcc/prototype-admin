"use client"

import { useCallback, useEffect, useState } from "react"
import { useCompanyId } from "@/hooks/company/useCompanyId"
import { apiFetch } from "@/lib/api/api-fetch"

export interface DepartmentItem {
  id: string
  name: string
  code?: string | null
  is_active?: boolean
}

/**
 * Hook canonical para listar departamentos da empresa.
 *
 * Usa o mesmo pattern de `useDepartmentManagement.saveDepartmentToAPI`:
 * `?company_id=${companyId}` quando POST (necessário para o gate canonical),
 * e GET via proxy authenticated. Backend resolve company_id via JWT.
 *
 * Retorna array de departamentos canonical para uso em multi-select
 * (e.g. BenefitFormModal). Mantém shape mínimo: id + name + code + is_active.
 */
export function useDepartmentsList() {
  const { companyId } = useCompanyId()
  const [departments, setDepartments] = useState<DepartmentItem[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchDepartments = useCallback(async () => {
    if (!companyId) {
      setDepartments([])
      return
    }
    setLoading(true)
    setError(null)
    try {
      const response = await apiFetch(
        `/api/backend-proxy/company/departments`
      )
      if (response.ok) {
        const data = await response.json()
        const list = Array.isArray(data) ? data : data?.items || []
        setDepartments(
          (list as Array<Record<string, unknown>>).map((d) => ({
            id: String(d.id ?? ""),
            name: String(d.name ?? ""),
            code: typeof d.code === "string" ? d.code : null,
            is_active: d.is_active !== false,
          })).filter((d) => d.id && d.name)
        )
      } else {
        setDepartments([])
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load departments")
      setDepartments([])
    } finally {
      setLoading(false)
    }
  }, [companyId])

  useEffect(() => {
    fetchDepartments()
  }, [fetchDepartments])

  return { departments, loading, error, refetch: fetchDepartments }
}
