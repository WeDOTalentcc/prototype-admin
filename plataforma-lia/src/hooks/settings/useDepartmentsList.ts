"use client"

import { useQuery } from "@tanstack/react-query"
import { useCompanyId } from "@/hooks/company/useCompanyId"
import { apiFetch } from "@/lib/api/api-fetch"
import { SETTINGS_QUERY_KEYS } from "@/hooks/settings/useSettingsBroadcast"

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

  const { data = [], isLoading, error, refetch } = useQuery<DepartmentItem[]>({
    queryKey: SETTINGS_QUERY_KEYS.departments(companyId ?? ""),
    queryFn: async () => {
      const response = await apiFetch("/api/backend-proxy/company/departments")
      if (!response.ok) return []
      const json = await response.json()
      const list = Array.isArray(json) ? json : json?.items || []
      return (list as Array<Record<string, unknown>>)
        .map((d) => ({
          id: String(d.id ?? ""),
          name: String(d.name ?? ""),
          code: typeof d.code === "string" ? d.code : null,
          is_active: d.is_active !== false,
        }))
        .filter((d) => d.id && d.name)
    },
    enabled: !!companyId,
    staleTime: 30_000,
  })

  return {
    departments: data,
    loading: isLoading,
    error: error instanceof Error ? error.message : null,
    refetch,
  }
}
